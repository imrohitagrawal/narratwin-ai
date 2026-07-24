"""Stage 6 multilingual walkthrough generation with mock/local providers."""

from __future__ import annotations

import base64
import binascii
import json
import logging
import re
import threading
from collections.abc import Iterable
from dataclasses import asdict, dataclass, replace
from datetime import timedelta
from pathlib import Path
from typing import Any, Literal, Protocol, cast

import langcodes
from babel import Locale
from pydub import AudioSegment  # type: ignore[import-untyped]
import srt  # type: ignore[import-untyped]

from backend.app.rag.chunking import checksum_text
from backend.app.storage import load_state, resolve_state_file, write_state
from backend.app.stage4 import contains_secret_like_content
from backend.app.stage7 import build_source_evaluation_checksum
from backend.app.tts_provider import (
    ElevenLabsTTSProvider,
    ExternalTTSResult,
    SUPPORTED_AUDIO_MIME_TYPES,
    TTSProviderError,
    checksum_bytes,
)

PRIORITY1_LANGUAGE_TAGS = (
    "en",
    "hi",
    "es",
    "de",
    "fr",
    "pt-BR",
    "it",
    "nl",
    "pl",
    "uk",
    "ru",
    "zh-Hans",
    "zh-Hant",
    "ja",
    "ko",
    "ar",
    "arz",
    "he",
    "fa",
    "tr",
    "vi",
    "id",
    "fil",
    "th",
    "ms",
)
PRIORITY2_LANGUAGE_TAGS = ("bn", "ta", "te", "kn", "mr", "gu", "ml", "ur", "pa")
SUPPORTED_LANGUAGES: dict[str, str] = {}
MAX_GLOSSARY_TERMS = 25
MAX_GLOSSARY_TERM_CHARS = 80
MAX_SOURCE_SCRIPT_CHARS = 20_000
MAX_STAGE6_ARTIFACT_BYTES = 512 * 1024
MAX_STAGE6_ARTIFACT_BASE64_CHARS = ((MAX_STAGE6_ARTIFACT_BYTES + 2) // 3) * 4
MAX_CAPTION_CHARS = 96
MAX_CAPTION_COUNT = 250
MAX_PROVIDER_ID_CHARS = 64
MAX_IDEMPOTENCY_RECORDS_PER_SCOPE = 100
PROVIDER_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")
CHECKSUM_COMPONENT_DELIMITER_PATTERN = re.compile(r"[\x00-\x1f\x7f,]")
LOGGER = logging.getLogger(__name__)
VOICE_MANIFEST_KEYS = frozenset(
    {
        "provider",
        "providerMode",
        "language",
        "languageDisplayName",
        "textChecksum",
        "durationSecondsEstimate",
        "mockAudioProfile",
        "disclosure",
    }
)
MOCK_AUDIO_PROFILE_KEYS = frozenset({"durationMillisecondsEstimate", "sampleRateHz", "channels"})
ProviderMode = Literal["LOCAL", "DISABLED", "OPTIONAL_EXTERNAL"]
EvaluationStatus = Literal["PASSED", "FAILED", "UNKNOWN"]


class Stage6Error(Exception):
    def __init__(self, status_code: int, code: str, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message


@dataclass(frozen=True)
class DownloadableArtifact:
    file_name: str
    mime_type: str
    content_base64: str
    checksum: str


@dataclass(frozen=True)
class LanguageCatalogRecord:
    language_tag: str
    english_name: str
    native_name: str
    script: str
    direction: Literal["ltr", "rtl"]
    market_priority: int
    region_group: str
    local_demo_support_status: Literal["SUPPORTED", "PLANNED_UNSUPPORTED_LOCAL_DEMO"]
    provider_support_status: Literal["LOCAL_DEMO_FIXTURE", "UNSUPPORTED_LOCAL_DEMO"]
    test_coverage_level: Literal["CHECKPOINT3A_EXHAUSTIVE", "CATALOG_ONLY"]


@dataclass(frozen=True)
class MultilingualTranscriptSegment:
    segment_id: str
    source_text: str
    target_language: str
    target_text: str
    english_reference_text: str
    citation_markers: tuple[str, ...]
    citation_indexes: tuple[int, ...]
    context_ref_ids: tuple[str, ...]
    claim_support_ids: tuple[str, ...]
    source_run_id: str
    evaluation_id: str


@dataclass(frozen=True)
class TranscriptCorrectness:
    validation_status: Literal["PASSED"]
    script: str
    direction: Literal["ltr", "rtl"]
    segment_count: int
    citation_indexes: tuple[int, ...]


LANGUAGE_CATALOG: tuple[LanguageCatalogRecord, ...] = (
    LanguageCatalogRecord(
        "en", "English", "English", "Latin", "ltr", 1, "Global", "SUPPORTED", "LOCAL_DEMO_FIXTURE", "CHECKPOINT3A_EXHAUSTIVE"
    ),
    LanguageCatalogRecord(
        "hi", "Hindi", "हिन्दी", "Devanagari", "ltr", 1, "South Asia", "SUPPORTED", "LOCAL_DEMO_FIXTURE", "CHECKPOINT3A_EXHAUSTIVE"
    ),
    LanguageCatalogRecord(
        "es", "Spanish", "Español", "Latin", "ltr", 1, "Europe/Latin America", "SUPPORTED", "LOCAL_DEMO_FIXTURE", "CHECKPOINT3A_EXHAUSTIVE"
    ),
    LanguageCatalogRecord(
        "de", "German", "Deutsch", "Latin", "ltr", 1, "Europe", "SUPPORTED", "LOCAL_DEMO_FIXTURE", "CHECKPOINT3A_EXHAUSTIVE"
    ),
    LanguageCatalogRecord(
        "fr", "French", "Français", "Latin", "ltr", 1, "Europe/Africa/Canada", "SUPPORTED", "LOCAL_DEMO_FIXTURE", "CHECKPOINT3A_EXHAUSTIVE"
    ),
    LanguageCatalogRecord(
        "pt-BR", "Brazilian Portuguese", "Português do Brasil", "Latin", "ltr", 1, "Latin America", "SUPPORTED", "LOCAL_DEMO_FIXTURE", "CHECKPOINT3A_EXHAUSTIVE"
    ),
    LanguageCatalogRecord(
        "it", "Italian", "Italiano", "Latin", "ltr", 1, "Europe", "SUPPORTED", "LOCAL_DEMO_FIXTURE", "CHECKPOINT3A_EXHAUSTIVE"
    ),
    LanguageCatalogRecord(
        "nl", "Dutch", "Nederlands", "Latin", "ltr", 1, "Europe", "SUPPORTED", "LOCAL_DEMO_FIXTURE", "CHECKPOINT3A_EXHAUSTIVE"
    ),
    LanguageCatalogRecord(
        "pl", "Polish", "Polski", "Latin", "ltr", 1, "Europe", "SUPPORTED", "LOCAL_DEMO_FIXTURE", "CHECKPOINT3A_EXHAUSTIVE"
    ),
    LanguageCatalogRecord(
        "uk", "Ukrainian", "Українська", "Cyrillic", "ltr", 1, "Europe", "SUPPORTED", "LOCAL_DEMO_FIXTURE", "CHECKPOINT3A_EXHAUSTIVE"
    ),
    LanguageCatalogRecord(
        "ru", "Russian", "Русский", "Cyrillic", "ltr", 1, "Europe/Asia", "SUPPORTED", "LOCAL_DEMO_FIXTURE", "CHECKPOINT3A_EXHAUSTIVE"
    ),
    LanguageCatalogRecord(
        "zh-Hans", "Chinese Simplified", "简体中文", "Han Simplified", "ltr", 1, "East Asia", "SUPPORTED", "LOCAL_DEMO_FIXTURE", "CHECKPOINT3A_EXHAUSTIVE"
    ),
    LanguageCatalogRecord(
        "zh-Hant", "Chinese Traditional", "繁體中文", "Han Traditional", "ltr", 1, "East Asia", "SUPPORTED", "LOCAL_DEMO_FIXTURE", "CHECKPOINT3A_EXHAUSTIVE"
    ),
    LanguageCatalogRecord(
        "ja", "Japanese", "日本語", "Japanese", "ltr", 1, "East Asia", "SUPPORTED", "LOCAL_DEMO_FIXTURE", "CHECKPOINT3A_EXHAUSTIVE"
    ),
    LanguageCatalogRecord(
        "ko", "Korean", "한국어", "Hangul", "ltr", 1, "East Asia", "SUPPORTED", "LOCAL_DEMO_FIXTURE", "CHECKPOINT3A_EXHAUSTIVE"
    ),
    LanguageCatalogRecord(
        "ar", "Arabic", "العربية", "Arabic", "rtl", 1, "MENA", "SUPPORTED", "LOCAL_DEMO_FIXTURE", "CHECKPOINT3A_EXHAUSTIVE"
    ),
    LanguageCatalogRecord(
        "arz", "Egyptian Arabic", "مصري", "Arabic", "rtl", 1, "MENA", "SUPPORTED", "LOCAL_DEMO_FIXTURE", "CHECKPOINT3A_EXHAUSTIVE"
    ),
    LanguageCatalogRecord(
        "he", "Hebrew", "עברית", "Hebrew", "rtl", 1, "MENA", "SUPPORTED", "LOCAL_DEMO_FIXTURE", "CHECKPOINT3A_EXHAUSTIVE"
    ),
    LanguageCatalogRecord(
        "fa", "Persian/Farsi", "فارسی", "Arabic", "rtl", 1, "MENA/Central Asia", "SUPPORTED", "LOCAL_DEMO_FIXTURE", "CHECKPOINT3A_EXHAUSTIVE"
    ),
    LanguageCatalogRecord(
        "tr", "Turkish", "Türkçe", "Latin", "ltr", 1, "Europe/West Asia", "SUPPORTED", "LOCAL_DEMO_FIXTURE", "CHECKPOINT3A_EXHAUSTIVE"
    ),
    LanguageCatalogRecord(
        "vi", "Vietnamese", "Tiếng Việt", "Latin", "ltr", 1, "Southeast Asia", "SUPPORTED", "LOCAL_DEMO_FIXTURE", "CHECKPOINT3A_EXHAUSTIVE"
    ),
    LanguageCatalogRecord(
        "id", "Indonesian", "Bahasa Indonesia", "Latin", "ltr", 1, "Southeast Asia", "SUPPORTED", "LOCAL_DEMO_FIXTURE", "CHECKPOINT3A_EXHAUSTIVE"
    ),
    LanguageCatalogRecord(
        "fil", "Filipino/Tagalog", "Filipino", "Latin", "ltr", 1, "Southeast Asia", "SUPPORTED", "LOCAL_DEMO_FIXTURE", "CHECKPOINT3A_EXHAUSTIVE"
    ),
    LanguageCatalogRecord(
        "th", "Thai", "ไทย", "Thai", "ltr", 1, "Southeast Asia", "SUPPORTED", "LOCAL_DEMO_FIXTURE", "CHECKPOINT3A_EXHAUSTIVE"
    ),
    LanguageCatalogRecord(
        "ms", "Malay", "Bahasa Melayu", "Latin", "ltr", 1, "Southeast Asia", "SUPPORTED", "LOCAL_DEMO_FIXTURE", "CHECKPOINT3A_EXHAUSTIVE"
    ),
    LanguageCatalogRecord(
        "bn", "Bengali", "বাংলা", "Bengali", "ltr", 2, "South Asia", "PLANNED_UNSUPPORTED_LOCAL_DEMO", "UNSUPPORTED_LOCAL_DEMO", "CATALOG_ONLY"
    ),
    LanguageCatalogRecord(
        "ta", "Tamil", "தமிழ்", "Tamil", "ltr", 2, "South Asia", "PLANNED_UNSUPPORTED_LOCAL_DEMO", "UNSUPPORTED_LOCAL_DEMO", "CATALOG_ONLY"
    ),
    LanguageCatalogRecord(
        "te", "Telugu", "తెలుగు", "Telugu", "ltr", 2, "South Asia", "PLANNED_UNSUPPORTED_LOCAL_DEMO", "UNSUPPORTED_LOCAL_DEMO", "CATALOG_ONLY"
    ),
    LanguageCatalogRecord(
        "kn", "Kannada", "ಕನ್ನಡ", "Kannada", "ltr", 2, "South Asia", "PLANNED_UNSUPPORTED_LOCAL_DEMO", "UNSUPPORTED_LOCAL_DEMO", "CATALOG_ONLY"
    ),
    LanguageCatalogRecord(
        "mr", "Marathi", "मराठी", "Devanagari", "ltr", 2, "South Asia", "PLANNED_UNSUPPORTED_LOCAL_DEMO", "UNSUPPORTED_LOCAL_DEMO", "CATALOG_ONLY"
    ),
    LanguageCatalogRecord(
        "gu", "Gujarati", "ગુજરાતી", "Gujarati", "ltr", 2, "South Asia", "PLANNED_UNSUPPORTED_LOCAL_DEMO", "UNSUPPORTED_LOCAL_DEMO", "CATALOG_ONLY"
    ),
    LanguageCatalogRecord(
        "ml", "Malayalam", "മലയാളം", "Malayalam", "ltr", 2, "South Asia", "PLANNED_UNSUPPORTED_LOCAL_DEMO", "UNSUPPORTED_LOCAL_DEMO", "CATALOG_ONLY"
    ),
    LanguageCatalogRecord(
        "ur", "Urdu", "اردو", "Arabic", "rtl", 2, "South Asia", "PLANNED_UNSUPPORTED_LOCAL_DEMO", "UNSUPPORTED_LOCAL_DEMO", "CATALOG_ONLY"
    ),
    LanguageCatalogRecord(
        "pa", "Punjabi", "ਪੰਜਾਬੀ", "Gurmukhi", "ltr", 2, "South Asia", "PLANNED_UNSUPPORTED_LOCAL_DEMO", "UNSUPPORTED_LOCAL_DEMO", "CATALOG_ONLY"
    ),
)
LANGUAGE_CATALOG_BY_TAG = {record.language_tag: record for record in LANGUAGE_CATALOG}
SUPPORTED_LANGUAGES.update(
    {
        record.language_tag: record.english_name
        for record in LANGUAGE_CATALOG
        if record.local_demo_support_status == "SUPPORTED"
    }
)
DEMO_TRANSLATED_SEGMENT_TEXT = {
    "hi": "NarraTwin AI स्वीकृत परियोजना-जानकारी को तथ्य-आधारित, चरण-दर-चरण प्रस्तुति की पटकथाओं में बदलता है।",
    "es": "NarraTwin AI convierte el conocimiento aprobado del proyecto en guiones de recorrido fundamentados con citas de origen.",
    "de": "NarraTwin AI wandelt genehmigtes Projektwissen in fundierte Präsentationsskripte mit Quellenzitaten um.",
    "fr": "NarraTwin AI transforme les connaissances approuvées du projet en scripts de présentation fondés avec des citations de source.",
    "pt-BR": "O NarraTwin AI transforma conhecimento aprovado do projeto em roteiros de apresentação fundamentados com citações de fonte.",
    "it": "NarraTwin AI trasforma la conoscenza approvata del progetto in copioni di presentazione fondati con citazioni delle fonti.",
    "nl": "NarraTwin AI zet goedgekeurde projectkennis om in onderbouwde presentatiescripts met broncitaten.",
    "pl": "NarraTwin AI przekształca zatwierdzoną wiedzę projektową w ugruntowane skrypty prezentacyjne z cytatami źródłowymi.",
    "uk": "NarraTwin AI перетворює затверджені знання про проект на обґрунтовані сценарії презентації з посиланнями на джерела.",
    "ru": "NarraTwin AI превращает утвержденные знания проекта в обоснованные сценарии презентации с ссылками на источники.",
    "zh-Hans": "NarraTwin AI 将已批准的项目知识转换为带有来源引用的有依据讲解脚本。",
    "zh-Hant": "NarraTwin AI 將已核准的專案知識轉換為帶有來源引用的有根據導覽腳本。",
    "ja": "NarraTwin AI は承認済みのプロジェクト知識を出典引用付きの根拠ある説明台本に変換します。",
    "ko": "NarraTwin AI는 승인된 프로젝트 지식을 출처 인용이 있는 근거 기반 설명 대본으로 변환합니다.",
    "ar": "يحوّل NarraTwin AI المعرفة المعتمدة للمشروع إلى نصوص شرح موثقة باقتباسات من المصدر.",
    "arz": "NarraTwin AI بيحوّل معرفة المشروع المعتمدة لنصوص شرح موثقة ومعاها اقتباسات من المصدر.",
    "he": "NarraTwin AI הופך ידע פרויקט מאושר לתסריטי הסבר מבוססים עם ציטוטי מקור.",
    "fa": "NarraTwin AI دانش تأییدشده پروژه را به متن‌های توضیحی مستند با ارجاع به منبع تبدیل می‌کند.",
    "tr": "NarraTwin AI, onaylanmış proje bilgisini kaynak alıntılı temellendirilmiş anlatım metinlerine dönüştürür.",
    "vi": "NarraTwin AI chuyển kiến thức dự án đã phê duyệt thành kịch bản hướng dẫn có căn cứ kèm trích dẫn nguồn.",
    "id": "NarraTwin AI mengubah pengetahuan proyek yang disetujui menjadi naskah panduan berlandaskan bukti dengan kutipan sumber.",
    "fil": "Ginagawang may-batayang script ng pagpapaliwanag ng NarraTwin AI ang aprubadong kaalaman sa proyekto na may sipi ng pinagmulan.",
    "th": "NarraTwin AI แปลงความรู้โครงการที่อนุมัติแล้วเป็นสคริปต์อธิบายที่มีหลักฐานพร้อมการอ้างอิงแหล่งที่มา",
    "ms": "NarraTwin AI menukar pengetahuan projek yang diluluskan kepada skrip penerangan berasas dengan petikan sumber.",
}
DEMO_AUDIENCE_SUPPORT_TEXT = {
    "hi": "यह भर्ती विशेषज्ञों, नियुक्ति प्रबंधकों, अभियंताओं, उत्पाद नेतृत्वकर्ताओं, ग्राहकों, नए उपयोगकर्ताओं और वैश्विक दर्शकों के लिए दर्शक-अनुरूप व्याख्याओं का समर्थन करता है।",
    "es": "Admite explicaciones adaptadas para reclutadores, responsables de contratación, ingenieros, líderes de producto, clientes, principiantes y audiencias globales.",
    "de": "Es unterstützt zielgruppengerechte Erklärungen für Personalvermittler, Einstellungsmanager, Ingenieure, Produktverantwortliche, Kunden, Einsteiger und globale Zielgruppen.",
    "fr": "Il prend en charge des explications adaptées aux recruteurs, responsables du recrutement, ingénieurs, responsables produit, clients, débutants et publics internationaux.",
    "pt-BR": "Ele oferece explicações adaptadas para recrutadores, gestores de contratação, engenheiros, líderes de produto, clientes, iniciantes e públicos globais.",
    "it": "Supporta spiegazioni adattate per selezionatori, responsabili delle assunzioni, ingegneri, responsabili di prodotto, clienti, principianti e pubblico globale.",
    "nl": "Het ondersteunt doelgroepgerichte uitleg voor wervers, wervingsmanagers, ingenieurs, productleiders, klanten, beginnende gebruikers en wereldwijde doelgroepen.",
    "pl": "Obsługuje wyjaśnienia dostosowane do rekruterów, menedżerów zatrudniających, inżynierów, liderów produktu, klientów, początkujących i odbiorców globalnych.",
    "uk": "Він підтримує пояснення, адаптовані для рекрутерів, менеджерів з найму, інженерів, продуктових лідерів, клієнтів, початківців і глобальних аудиторій.",
    "ru": "Он поддерживает объяснения, адаптированные для рекрутеров, менеджеров по найму, инженеров, продуктовых лидеров, клиентов, начинающих и глобальной аудитории.",
    "zh-Hans": "它支持面向招聘人员、招聘经理、工程师、产品负责人、客户、初学者和全球受众的受众化说明。",
    "zh-Hant": "它支援面向招募人員、招募經理、工程師、產品負責人、客戶、初學者和全球受眾的受眾化說明。",
    "ja": "採用担当者、採用責任者、エンジニア、プロダクトリーダー、顧客、初心者、世界中の視聴者に合わせた説明をサポートします。",
    "ko": "채용 담당자, 채용 관리자, 엔지니어, 제품 리더, 고객, 초보자, 전 세계 시청자를 위한 대상별 설명을 지원합니다.",
    "ar": "يدعم شروحات مخصصة لمسؤولي التوظيف ومديري التوظيف والمهندسين وقادة المنتج والعملاء والمبتدئين والجماهير العالمية.",
    "arz": "بيدعم شروحات مناسبة لمسؤولي التوظيف ومديري التوظيف والمهندسين وقادة المنتج والعملاء والمبتدئين والجمهور العالمي.",
    "he": "הוא תומך בהסברים מותאמי קהל עבור מגייסים, מנהלי גיוס, מהנדסים, מובילי מוצר, לקוחות, מתחילים וצופים גלובליים.",
    "fa": "از توضیح‌های متناسب با جذب‌کنندگان نیرو، مدیران استخدام، مهندسان، رهبران محصول، مشتریان، کاربران تازه‌کار و مخاطبان جهانی پشتیبانی می‌کند.",
    "tr": "İşe alım uzmanları, işe alım yöneticileri, mühendisler, ürün liderleri, müşteriler, yeni başlayanlar ve küresel kitleler için hedef kitleye uyarlanmış açıklamaları destekler.",
    "vi": "Nó hỗ trợ phần giải thích phù hợp cho nhà tuyển dụng, quản lý tuyển dụng, kỹ sư, lãnh đạo sản phẩm, khách hàng, người mới và khán giả toàn cầu.",
    "id": "Ini mendukung penjelasan yang disesuaikan untuk perekrut, manajer perekrutan, insinyur, pemimpin produk, pelanggan, pemula, dan audiens global.",
    "fil": "Sinusuportahan nito ang mga paliwanag na angkop sa mga tagapagrekrut, tagapamahala sa pagkuha, inhinyero, lider ng produkto, kliyente, baguhan, at pandaigdigang manonood.",
    "th": "รองรับคำอธิบายที่ปรับให้เหมาะกับผู้สรรหาบุคลากร ผู้จัดการฝ่ายสรรหา วิศวกร ผู้นำผลิตภัณฑ์ ลูกค้า ผู้เริ่มต้น และผู้ชมทั่วโลก",
    "ms": "Ia menyokong penerangan yang disesuaikan untuk perekrut, pengurus pengambilan pekerja, jurutera, pemimpin produk, pelanggan, pemula dan penonton global.",
}
DEMO_RECRUITER_ENGINEERING_SUPPORT_TEXT = {
    "hi": "यह भर्ती विशेषज्ञों और अभियांत्रिकी दर्शकों के लिए दर्शक-अनुरूप व्याख्याओं का समर्थन करता है।",
    "es": "Admite explicaciones adaptadas para audiencias de reclutadores e ingeniería.",
    "de": "Es unterstützt zielgruppengerechte Erklärungen für Personalvermittlungs- und Ingenieurzielgruppen.",
    "fr": "Il prend en charge des explications adaptées aux publics du recrutement et de l'ingénierie.",
    "pt-BR": "Ele oferece explicações adaptadas para públicos de recrutamento e engenharia.",
    "it": "Supporta spiegazioni adattate per il pubblico della selezione e dell'ingegneria.",
    "nl": "Het ondersteunt doelgroepgerichte uitleg voor werving en ingenieursdoelgroepen.",
    "pl": "Obsługuje wyjaśnienia dostosowane do odbiorców rekrutacyjnych i inżynieryjnych.",
    "uk": "Він підтримує пояснення, адаптовані для рекрутерської та інженерної аудиторій.",
    "ru": "Он поддерживает объяснения, адаптированные для рекрутерской и инженерной аудиторий.",
    "zh-Hans": "它支持面向招聘和工程受众的简明受众化说明。",
    "zh-Hant": "它支援專門面向招募和工程受眾的受眾化說明。",
    "ja": "採用担当者とエンジニアリングの視聴者に合わせた説明をサポートします。",
    "ko": "채용 담당자와 엔지니어링 대상자를 위한 대상별 설명을 지원합니다.",
    "ar": "يدعم شروحات مخصصة لجمهور التوظيف والهندسة.",
    "arz": "بيدعم شروحات مناسبة لجمهور التوظيف والهندسة.",
    "he": "הוא תומך בהסברים מותאמי קהל עבור קהלי גיוס והנדסה.",
    "fa": "از توضیح‌های متناسب با مخاطبان جذب نیرو و مهندسی پشتیبانی می‌کند.",
    "tr": "İşe alım ve mühendislik kitleleri için hedef kitleye uyarlanmış açıklamaları destekler.",
    "vi": "Nó hỗ trợ phần giải thích phù hợp cho nhóm tuyển dụng và kỹ thuật.",
    "id": "Ini mendukung penjelasan yang disesuaikan untuk audiens perekrutan dan teknik.",
    "fil": "Sinusuportahan nito ang mga paliwanag na angkop sa mga tagapakinig sa pangangalap ng tauhan at inhinyeriya.",
    "th": "รองรับคำอธิบายที่ปรับให้เหมาะกับกลุ่มผู้สรรหาบุคลากรและวิศวกรรม",
    "ms": "Ia menyokong penerangan yang disesuaikan untuk khalayak perekrutan dan kejuruteraan.",
}
DEMO_LOCAL_PROVIDER_TEXT = {
    "hi": "स्थानीय प्रदर्शन निर्धारक समीक्षा के लिए अनुकरणीय स्थानीय LLM, अनुवाद, आवाज़ और अवतार अनुकूलकों का उपयोग करता है।",
    "es": "La demostración local usa adaptadores locales simulados de LLM, traducción, voz y avatar para una revisión determinista.",
    "de": "Die lokale Demonstration nutzt simulierte lokale LLM-, Übersetzungs-, Sprach- und Avatar-Schnittstellen für deterministische Prüfungen.",
    "fr": "La démonstration locale utilise des adaptateurs locaux simulés de LLM, de traduction, de voix et d'avatar pour une revue déterministe.",
    "pt-BR": "A demonstração local usa adaptadores locais simulados de LLM, tradução, voz e avatar para revisão determinística.",
    "it": "La dimostrazione locale usa connettori locali simulati per LLM, traduzione, voce e avatar per una revisione deterministica.",
    "nl": "De lokale demonstratie gebruikt gesimuleerde lokale LLM-, vertaal-, stem- en avatar-koppelingen voor deterministische beoordeling.",
    "pl": "Lokalna demonstracja używa symulowanych lokalnych interfejsów LLM, tłumaczenia, głosu i awatara do deterministycznego przeglądu.",
    "uk": "Локальна демонстрація використовує макетні локальні адаптери LLM, перекладу, голосу й аватара для детермінованої перевірки.",
    "ru": "Локальная демонстрация использует имитированные локальные адаптеры LLM, перевода, голоса и аватара для детерминированной проверки.",
    "zh-Hans": "本地演示使用模拟的本地 LLM、翻译、语音和头像适配器，以便进行简明确定性审查。",
    "zh-Hant": "本機示範使用模擬的本機 LLM、翻譯、語音和頭像配接器，以便進行專門的確定性審查。",
    "ja": "ローカル実演は、決定論的な検証のために模擬ローカル LLM、翻訳、音声、仮想人物連携機能を使用します。",
    "ko": "로컬 시연은 결정론적 검토를 위해 모의 로컬 LLM, 번역, 음성, 가상 발표자 연결 구성 요소를 사용합니다.",
    "ar": "يستخدم العرض المحلي محولات محلية وهمية للنموذج اللغوي والترجمة والصوت والشخصية الافتراضية من أجل مراجعة حتمية.",
    "arz": "العرض المحلي بيستخدم محولات محلية وهمية للنموذج اللغوي والترجمة والصوت والشخصية الافتراضية علشان مراجعة حتمية.",
    "he": "ההדגמה המקומית משתמשת ברכיבי חיבור מקומיים מדומים עבור LLM, תרגום, קול ודמות וירטואלית לצורך סקירה קבועה מראש.",
    "fa": "نمایش محلی برای بازبینی قطعی از رابط‌های محلی شبیه‌سازی‌شده LLM، ترجمه، صدا و نمایه مجازی استفاده می‌کند.",
    "tr": "Yerel tanıtım, belirlenimci inceleme için sahte yerel LLM, çeviri, ses ve sanal karakter bağdaştırıcıları kullanır.",
    "vi": "Bản trình diễn cục bộ dùng các bộ điều hợp LLM, dịch thuật, giọng nói và hình đại diện cục bộ giả lập để đánh giá xác định.",
    "id": "Demonstrasi lokal menggunakan penghubung LLM, terjemahan, suara, dan figur virtual lokal tiruan untuk tinjauan yang hasilnya tetap.",
    "fil": "Gumagamit ang lokal na pagpapakita ng mga kunwaring lokal na tagapag-ugnay para sa LLM, pagsasalin, boses, at biswal na kinatawan para sa pagsusuring tiyak ang resulta.",
    "th": "การสาธิตภายในเครื่องใช้ตัวแปลง LLM การแปล เสียง และตัวแทนเสมือนแบบจำลองภายในเครื่องเพื่อการตรวจสอบที่กำหนดผลได้",
    "ms": "Demonstrasi tempatan menggunakan penyesuai LLM, terjemahan, suara dan watak maya tempatan olok-olok untuk semakan yang hasilnya tetap.",
}
DEMO_STAGE4_SLICE_TEXT = {
    "hi": "Stage 4 का भाग निर्धारक परीक्षणों के लिए अनुकरणीय स्थानीय LLM और अनुकरणीय स्थानीय अंतर्निवेशन का उपयोग करता है।",
    "es": "El segmento de Stage 4 usa un LLM local simulado y embeddings locales simulados para pruebas deterministas.",
    "de": "Der Stage-4-Teil nutzt ein simuliertes lokales LLM und simulierte lokale Vektordarstellungen für deterministische Tests.",
    "fr": "Le segment Stage 4 utilise un LLM local simulé et des représentations vectorielles locales simulées pour des tests déterministes.",
    "pt-BR": "A fatia Stage 4 usa um LLM local simulado e embeddings locais simulados para testes determinísticos.",
    "it": "La sezione Stage 4 usa un LLM locale simulato e rappresentazioni vettoriali locali simulate per test deterministici.",
    "nl": "Het Stage 4-onderdeel gebruikt een gesimuleerde lokale LLM en gesimuleerde lokale vectorrepresentaties voor deterministische tests.",
    "pl": "Wycinek Stage 4 używa symulowanego lokalnego LLM oraz symulowanych lokalnych reprezentacji wektorowych do testów deterministycznych.",
    "uk": "Зріз Stage 4 використовує макетний локальний LLM і макетні локальні векторні представлення для детермінованих тестів.",
    "ru": "Срез Stage 4 использует имитированный локальный LLM и имитированные локальные векторные представления для детерминированных тестов.",
    "zh-Hans": "Stage 4 切片使用模拟的本地 LLM 和模拟的本地嵌入来进行确定性测试。",
    "zh-Hant": "Stage 4 切片使用模擬的本機 LLM 和模擬的本機嵌入來進行確定性測試。",
    "ja": "Stage 4 の部分は、決定論的なテストのために模擬ローカル LLM と模擬ローカル埋め込みを使用します。",
    "ko": "Stage 4 부분은 결정론적 테스트를 위해 모의 로컬 LLM과 모의 로컬 벡터 표현을 사용합니다.",
    "ar": "تستخدم شريحة Stage 4 نموذجًا لغويًا محليًا وهميًا وتضمينات محلية وهمية للاختبارات الحتمية.",
    "arz": "شريحة Stage 4 بتستخدم نموذج لغوي محلي وهمي وتضمينات محلية وهمية للاختبارات الحتمية.",
    "he": "פרוסת Stage 4 משתמשת ב-LLM מקומי מדומה ובהטמעות מקומיות מדומות לבדיקות דטרמיניסטיות.",
    "fa": "بخش Stage 4 برای آزمون‌های قطعی از LLM محلی شبیه‌سازی‌شده و بازنمایی‌های برداری محلی شبیه‌سازی‌شده استفاده می‌کند.",
    "tr": "Stage 4 dilimi, deterministik testler için sahte yerel LLM ve sahte yerel gömmeler kullanır.",
    "vi": "Lát cắt Stage 4 dùng LLM cục bộ giả lập và embedding cục bộ giả lập cho các kiểm thử xác định.",
    "id": "Irisan Stage 4 menggunakan LLM lokal tiruan dan representasi vektor lokal tiruan untuk pengujian yang hasilnya tetap.",
    "fil": "Gumagamit ang bahagi ng Stage 4 ng kunwaring lokal na LLM at kunwaring lokal na representasyong vector para sa pagsusuring tiyak ang resulta.",
    "th": "ส่วน Stage 4 ใช้ LLM ภายในเครื่องแบบจำลองและการฝังข้อมูลภายในเครื่องแบบจำลองสำหรับการทดสอบที่กำหนดผลได้",
    "ms": "Bahagian Stage 4 menggunakan LLM tempatan olok-olok dan perwakilan vektor tempatan olok-olok untuk ujian yang hasilnya tetap.",
}
DEMO_CITATION_REQUIREMENT_TEXT = {
    "hi": "प्रत्येक उत्पन्न चरण-दर-चरण प्रस्तुति संबंधी दावे में स्वीकृत जानकारी से प्राप्त स्रोत अंशों का उद्धरण होना चाहिए।",
    "es": "Cada afirmación generada del recorrido debe citar fragmentos de fuente recuperados de conocimiento aprobado.",
    "de": "Jede generierte Aussage in der Präsentation muss abgerufene Quellenausschnitte aus genehmigtem Wissen zitieren.",
    "fr": "Chaque affirmation de démonstration générée doit citer les extraits source récupérés depuis les connaissances approuvées.",
    "pt-BR": "Toda afirmação gerada no roteiro deve citar trechos de fonte recuperados do conhecimento aprovado.",
    "it": "Ogni affermazione generata nel percorso deve citare frammenti di fonte recuperati dalla conoscenza approvata.",
    "nl": "Elke gegenereerde presentatieclaim moet opgehaalde bronfragmenten uit goedgekeurde kennis citeren.",
    "pl": "Każde wygenerowane twierdzenie w prezentacji musi cytować pobrane fragmenty źródłowe z zatwierdzonej wiedzy.",
    "uk": "Кожне згенероване твердження у поясненні має цитувати отримані фрагменти джерел із затверджених знань.",
    "ru": "Каждое сгенерированное утверждение в пояснении должно цитировать извлеченные фрагменты источников из утвержденных знаний.",
    "zh-Hans": "每个生成的简明讲解声明都必须引用从已批准知识中检索到的来源片段。",
    "zh-Hant": "每個產生的專門導覽聲明都必須引用從已核准知識中擷取到的來源片段。",
    "ja": "生成された各説明の主張は、承認済み知識から取得した出典部分を引用しなければなりません。",
    "ko": "생성된 모든 안내 주장에는 승인된 지식에서 검색된 출처 조각을 인용해야 합니다.",
    "ar": "يجب أن يستشهد كل ادعاء إرشادي يتم إنشاؤه بمقاطع مصدر مسترجعة من المعرفة المعتمدة.",
    "arz": "كل ادعاء شرح متولد لازم يستشهد بمقاطع مصدر مسترجعة من المعرفة المعتمدة.",
    "he": "כל טענת הדרכה שנוצרת חייבת לצטט מקטעי מקור שאוחזרו מידע מאושר.",
    "fa": "هر ادعای راهنمای تولیدشده باید بخش‌های منبع بازیابی‌شده از دانش تأییدشده را ارجاع دهد.",
    "tr": "Üretilen her anlatım iddiası, onaylanmış bilgiden alınan kaynak parçalarına atıf yapmalıdır.",
    "vi": "Mỗi tuyên bố hướng dẫn được tạo phải trích dẫn các đoạn nguồn được truy xuất từ kiến thức đã phê duyệt.",
    "id": "Setiap klaim panduan yang dihasilkan harus mengutip potongan sumber yang diambil dari pengetahuan yang disetujui.",
    "fil": "Dapat sipiin ng bawat nabuong pahayag sa pagpapaliwanag ang mga bahagi ng pinagmulan na nakuha mula sa aprubadong kaalaman.",
    "th": "ทุกข้อกล่าวอ้างในคำแนะนำที่สร้างขึ้นต้องอ้างอิงส่วนแหล่งข้อมูลที่ดึงมาจากความรู้ที่อนุมัติแล้ว",
    "ms": "Setiap dakwaan panduan yang dijana mesti memetik cebisan sumber yang diperoleh daripada pengetahuan yang diluluskan.",
}
DEMO_AUDIENCE_PREFIX_TEXT = {
    "hi": {
        "recruiters": "भर्ती विशेषज्ञों के लिए",
        "hiring managers": "नियुक्ति प्रबंधकों के लिए",
        "engineers": "अभियंताओं के लिए",
        "product leaders": "उत्पाद नेतृत्वकर्ताओं के लिए",
        "beginners": "नए उपयोगकर्ताओं के लिए",
        "global viewers": "वैश्विक दर्शकों के लिए",
        "customers": "ग्राहकों के लिए",
    },
    "es": {
        "recruiters": "Para reclutadores",
        "hiring managers": "Para responsables de contratación",
        "engineers": "Para ingenieros",
        "product leaders": "Para líderes de producto",
        "beginners": "Para principiantes",
        "global viewers": "Para audiencias globales",
        "customers": "Para clientes",
    },
    "de": {
        "recruiters": "Für Personalvermittler",
        "hiring managers": "Für Einstellungsmanager",
        "engineers": "Für Ingenieure",
        "product leaders": "Für Produktverantwortliche",
        "beginners": "Für Einsteiger",
        "global viewers": "Für globale Zuschauer",
        "customers": "Für Kunden",
    },
    "fr": {
        "recruiters": "Pour les recruteurs",
        "hiring managers": "Pour les responsables du recrutement",
        "engineers": "Pour les ingénieurs",
        "product leaders": "Pour les responsables produit",
        "beginners": "Pour les débutants",
        "global viewers": "Pour les publics internationaux",
        "customers": "Pour les clients",
    },
    "pt-BR": {
        "recruiters": "Para recrutadores",
        "hiring managers": "Para gestores de contratação",
        "engineers": "Para engenheiros",
        "product leaders": "Para líderes de produto",
        "beginners": "Para iniciantes",
        "global viewers": "Para públicos globais",
        "customers": "Para clientes",
    },
    "it": {
        "recruiters": "Per i selezionatori",
        "hiring managers": "Per i responsabili delle assunzioni",
        "engineers": "Per gli ingegneri",
        "product leaders": "Per i responsabili di prodotto",
        "beginners": "Per i principianti",
        "global viewers": "Per il pubblico globale",
        "customers": "Per i clienti",
    },
    "nl": {
        "recruiters": "Voor wervers",
        "hiring managers": "Voor wervingsmanagers",
        "engineers": "Voor ingenieurs",
        "product leaders": "Voor productleiders",
        "beginners": "Voor beginnende gebruikers",
        "global viewers": "Voor wereldwijde kijkers",
        "customers": "Voor klanten",
    },
    "pl": {
        "recruiters": "Dla rekruterów",
        "hiring managers": "Dla menedżerów zatrudniających",
        "engineers": "Dla inżynierów",
        "product leaders": "Dla liderów produktu",
        "beginners": "Dla początkujących",
        "global viewers": "Dla odbiorców globalnych",
        "customers": "Dla klientów",
    },
    "uk": {
        "recruiters": "Для рекрутерів",
        "hiring managers": "Для менеджерів з найму",
        "engineers": "Для інженерів",
        "product leaders": "Для продуктових лідерів",
        "beginners": "Для початківців",
        "global viewers": "Для глобальних глядачів",
        "customers": "Для клієнтів",
    },
    "ru": {
        "recruiters": "Для рекрутеров",
        "hiring managers": "Для менеджеров по найму",
        "engineers": "Для инженеров",
        "product leaders": "Для продуктовых лидеров",
        "beginners": "Для начинающих",
        "global viewers": "Для глобальных зрителей",
        "customers": "Для клиентов",
    },
    "zh-Hans": {
        "recruiters": "面向招聘人员",
        "hiring managers": "面向招聘经理",
        "engineers": "面向工程师",
        "product leaders": "面向产品负责人",
        "beginners": "面向初学者",
        "global viewers": "面向全球观众",
        "customers": "面向客户",
    },
    "zh-Hant": {
        "recruiters": "面向招募人員",
        "hiring managers": "面向招募經理",
        "engineers": "面向工程師",
        "product leaders": "面向產品負責人",
        "beginners": "面向初學者",
        "global viewers": "面向全球觀眾",
        "customers": "面向客戶",
    },
    "ja": {
        "recruiters": "採用担当者向けに",
        "hiring managers": "採用責任者向けに",
        "engineers": "エンジニア向けに",
        "product leaders": "プロダクトリーダー向けに",
        "beginners": "初心者向けに",
        "global viewers": "世界中の視聴者向けに",
        "customers": "顧客向けに",
    },
    "ko": {
        "recruiters": "채용 담당자를 위해",
        "hiring managers": "채용 관리자를 위해",
        "engineers": "엔지니어를 위해",
        "product leaders": "제품 리더를 위해",
        "beginners": "초보자를 위해",
        "global viewers": "전 세계 시청자를 위해",
        "customers": "고객을 위해",
    },
    "ar": {
        "recruiters": "لمسؤولي التوظيف",
        "hiring managers": "لمديري التوظيف",
        "engineers": "للمهندسين",
        "product leaders": "لقادة المنتج",
        "beginners": "للمبتدئين",
        "global viewers": "للمشاهدين العالميين",
        "customers": "للعملاء",
    },
    "arz": {
        "recruiters": "لمسؤولي التوظيف",
        "hiring managers": "لمديري التوظيف",
        "engineers": "للمهندسين",
        "product leaders": "لقادة المنتج",
        "beginners": "للمبتدئين",
        "global viewers": "للمشاهدين العالميين",
        "customers": "للعملاء",
    },
    "he": {
        "recruiters": "עבור מגייסים",
        "hiring managers": "עבור מנהלי גיוס",
        "engineers": "עבור מהנדסים",
        "product leaders": "עבור מובילי מוצר",
        "beginners": "עבור מתחילים",
        "global viewers": "עבור צופים גלובליים",
        "customers": "עבור לקוחות",
    },
    "fa": {
        "recruiters": "برای جذب‌کنندگان نیرو",
        "hiring managers": "برای مدیران استخدام",
        "engineers": "برای مهندسان",
        "product leaders": "برای رهبران محصول",
        "beginners": "برای کاربران تازه‌کار",
        "global viewers": "برای مخاطبان جهانی",
        "customers": "برای مشتریان",
    },
    "tr": {
        "recruiters": "İşe alım uzmanları için",
        "hiring managers": "İşe alım yöneticileri için",
        "engineers": "Mühendisler için",
        "product leaders": "Ürün liderleri için",
        "beginners": "Yeni başlayanlar için",
        "global viewers": "Küresel izleyiciler için",
        "customers": "Müşteriler için",
    },
    "vi": {
        "recruiters": "Dành cho nhà tuyển dụng",
        "hiring managers": "Dành cho quản lý tuyển dụng",
        "engineers": "Dành cho kỹ sư",
        "product leaders": "Dành cho lãnh đạo sản phẩm",
        "beginners": "Dành cho người mới",
        "global viewers": "Dành cho khán giả toàn cầu",
        "customers": "Dành cho khách hàng",
    },
    "id": {
        "recruiters": "Untuk perekrut",
        "hiring managers": "Untuk manajer perekrutan",
        "engineers": "Untuk insinyur",
        "product leaders": "Untuk pemimpin produk",
        "beginners": "Untuk pemula",
        "global viewers": "Untuk pemirsa global",
        "customers": "Untuk pelanggan",
    },
    "fil": {
        "recruiters": "Para sa mga tagapagrekrut",
        "hiring managers": "Para sa mga tagapamahala sa pagkuha",
        "engineers": "Para sa mga inhinyero",
        "product leaders": "Para sa mga lider ng produkto",
        "beginners": "Para sa mga baguhan",
        "global viewers": "Para sa pandaigdigang manonood",
        "customers": "Para sa mga kliyente",
    },
    "th": {
        "recruiters": "สำหรับผู้สรรหาบุคลากร",
        "hiring managers": "สำหรับผู้จัดการฝ่ายสรรหา",
        "engineers": "สำหรับวิศวกร",
        "product leaders": "สำหรับผู้นำผลิตภัณฑ์",
        "beginners": "สำหรับผู้เริ่มต้น",
        "global viewers": "สำหรับผู้ชมทั่วโลก",
        "customers": "สำหรับลูกค้า",
    },
    "ms": {
        "recruiters": "Untuk perekrut",
        "hiring managers": "Untuk pengurus pengambilan pekerja",
        "engineers": "Untuk jurutera",
        "product leaders": "Untuk pemimpin produk",
        "beginners": "Untuk pemula",
        "global viewers": "Untuk penonton global",
        "customers": "Untuk pelanggan",
    },
}
ATLAS_OUTPUT_TRANSLATED_SEGMENT_TEXT = {
    "hi": "Atlas Output OUTPUT-SENTINEL-CP2 जारी करने के पूर्वाभ्यासों के लिए एक काल्पनिक स्थानीय जाँच-सूची निर्माता है।",
    "es": "Atlas Output OUTPUT-SENTINEL-CP2 es un creador local ficticio de listas de verificación para ensayos de lanzamiento.",
    "de": "Atlas Output OUTPUT-SENTINEL-CP2 ist ein fiktiver lokaler Ersteller von Prüflisten für Einführungsproben.",
    "fr": "Atlas Output OUTPUT-SENTINEL-CP2 est un générateur local fictif de listes de contrôle pour les répétitions de lancement.",
    "pt-BR": "O Atlas Output OUTPUT-SENTINEL-CP2 é um criador local fictício de listas de verificação para ensaios de lançamento.",
    "it": "Atlas Output OUTPUT-SENTINEL-CP2 è un generatore locale fittizio di liste di controllo per le prove di lancio.",
    "nl": "Atlas Output OUTPUT-SENTINEL-CP2 is een fictieve lokale maker van controlelijsten voor lanceringsrepetities.",
    "pl": "Atlas Output OUTPUT-SENTINEL-CP2 jest fikcyjnym lokalnym narzędziem do tworzenia list kontrolnych na próby uruchomienia.",
    "uk": "Atlas Output OUTPUT-SENTINEL-CP2 є вигаданим локальним конструктором контрольних списків для репетицій запуску.",
    "ru": "Atlas Output OUTPUT-SENTINEL-CP2 — это вымышленный локальный конструктор контрольных списков для репетиций запуска.",
    "zh-Hans": "Atlas Output OUTPUT-SENTINEL-CP2 是用于发布演练的虚构本地检查清单生成器。",
    "zh-Hant": "Atlas Output OUTPUT-SENTINEL-CP2 是用於發布演練的虛構本機檢查清單產生器。",
    "ja": "Atlas Output OUTPUT-SENTINEL-CP2 は公開リハーサル用の架空のローカル確認リスト作成ツールです。",
    "ko": "Atlas Output OUTPUT-SENTINEL-CP2는 출시 예행연습용 가상 로컬 확인 목록 생성 도구입니다.",
    "ar": "Atlas Output OUTPUT-SENTINEL-CP2 هو منشئ محلي خيالي لقوائم التحقق الخاصة بتدريبات الإطلاق.",
    "arz": "Atlas Output OUTPUT-SENTINEL-CP2 هو منشئ محلي خيالي لقوايم التحقق الخاصة ببروفات الإطلاق.",
    "he": "Atlas Output OUTPUT-SENTINEL-CP2 הוא יוצר רשימות בדיקה מקומי בדיוני לחזרות השקה.",
    "fa": "Atlas Output OUTPUT-SENTINEL-CP2 یک سازنده محلی خیالی فهرست‌های بررسی برای تمرین‌های راه‌اندازی است.",
    "tr": "Atlas Output OUTPUT-SENTINEL-CP2, yayıma hazırlık provaları için kurgusal bir yerel denetim listesi oluşturucusudur.",
    "vi": "Atlas Output OUTPUT-SENTINEL-CP2 là trình tạo danh sách kiểm tra cục bộ giả định cho các buổi diễn tập ra mắt.",
    "id": "Atlas Output OUTPUT-SENTINEL-CP2 adalah pembuat daftar periksa lokal fiktif untuk latihan peluncuran.",
    "fil": "Ang Atlas Output OUTPUT-SENTINEL-CP2 ay kathang-isip na lokal na tagabuo ng talaang-suri para sa mga pagsasanay sa paglulunsad.",
    "th": "Atlas Output OUTPUT-SENTINEL-CP2 เป็นเครื่องมือสร้างรายการตรวจสอบภายในเครื่องแบบสมมติสำหรับการซ้อมเปิดตัว",
    "ms": "Atlas Output OUTPUT-SENTINEL-CP2 ialah pembina senarai semak tempatan rekaan untuk latihan pelancaran.",
}
ATLAS_OUTPUT_CITATION_TRANSLATED_SEGMENT_TEXT = {
    "hi": "Atlas Output OUTPUT-SENTINEL-CP2 के लिए प्रत्येक उत्पन्न जाँच-सूची मद में स्वीकृत जारीकरण-टिप्पणी प्रमाण का उद्धरण होना आवश्यक है।",
    "es": "Atlas Output OUTPUT-SENTINEL-CP2 exige que cada elemento generado de la lista de verificación cite evidencia aprobada de notas de lanzamiento.",
    "de": "Atlas Output OUTPUT-SENTINEL-CP2 verlangt, dass jeder erzeugte Prüflisteneintrag genehmigte Nachweise aus Einführungsnotizen zitiert.",
    "fr": "Atlas Output OUTPUT-SENTINEL-CP2 exige que chaque élément généré de la liste de contrôle cite des preuves approuvées issues des notes de lancement.",
    "pt-BR": "O Atlas Output OUTPUT-SENTINEL-CP2 exige que cada item gerado da lista de verificação cite evidências aprovadas das notas de lançamento.",
    "it": "Atlas Output OUTPUT-SENTINEL-CP2 richiede che ogni voce generata della lista di controllo citi prove approvate dalle note di lancio.",
    "nl": "Atlas Output OUTPUT-SENTINEL-CP2 vereist dat elk gegenereerd controlelijstitem goedgekeurd bewijs uit lanceringsnotities citeert.",
    "pl": "Atlas Output OUTPUT-SENTINEL-CP2 wymaga, aby każdy wygenerowany element listy kontrolnej cytował zatwierdzone dowody z notatek uruchomieniowych.",
    "uk": "Atlas Output OUTPUT-SENTINEL-CP2 вимагає, щоб кожен згенерований пункт контрольного списку цитував затверджені докази з нотаток запуску.",
    "ru": "Atlas Output OUTPUT-SENTINEL-CP2 требует, чтобы каждый сгенерированный пункт контрольного списка цитировал утвержденные доказательства из заметок запуска.",
    "zh-Hans": "Atlas Output OUTPUT-SENTINEL-CP2 要求每个生成的检查清单项目引用已批准的发布说明证据。",
    "zh-Hant": "Atlas Output OUTPUT-SENTINEL-CP2 要求每個產生的檢查清單項目引用已核准的發布說明證據。",
    "ja": "Atlas Output OUTPUT-SENTINEL-CP2 では、生成された各確認リスト項目が承認済みの公開メモの根拠を引用する必要があります。",
    "ko": "Atlas Output OUTPUT-SENTINEL-CP2는 생성된 각 확인 목록 항목이 승인된 출시 노트 증거를 인용하도록 요구합니다.",
    "ar": "يتطلب Atlas Output OUTPUT-SENTINEL-CP2 أن يستشهد كل عنصر منشأ في قائمة التحقق بأدلة معتمدة من ملاحظات الإطلاق.",
    "arz": "يتطلب Atlas Output OUTPUT-SENTINEL-CP2 إن كل عنصر متولد في قايمة التحقق يستشهد بأدلة معتمدة من ملاحظات الإطلاق.",
    "he": "Atlas Output OUTPUT-SENTINEL-CP2 דורש שכל פריט רשימת בדיקה שנוצר יצטט ראיות מאושרות מהערות השקה.",
    "fa": "Atlas Output OUTPUT-SENTINEL-CP2 الزام می‌کند که هر مورد فهرست بررسی تولیدشده شواهد تأییدشده از یادداشت‌های راه‌اندازی را ارجاع دهد.",
    "tr": "Atlas Output OUTPUT-SENTINEL-CP2, oluşturulan her denetim listesi maddesinin onaylanmış yayıma hazırlık notu kanıtlarına atıf yapmasını gerektirir.",
    "vi": "Atlas Output OUTPUT-SENTINEL-CP2 yêu cầu mỗi mục danh sách kiểm tra được tạo phải trích dẫn bằng chứng đã phê duyệt từ ghi chú ra mắt.",
    "id": "Atlas Output OUTPUT-SENTINEL-CP2 mewajibkan setiap item daftar periksa yang dihasilkan mengutip bukti catatan peluncuran yang disetujui.",
    "fil": "Inaatas ng Atlas Output OUTPUT-SENTINEL-CP2 na sipiin ng bawat nabuong talaang-suri ang aprubadong ebidensiya mula sa mga tala sa paglulunsad.",
    "th": "Atlas Output OUTPUT-SENTINEL-CP2 กำหนดให้แต่ละรายการตรวจสอบที่สร้างขึ้นต้องอ้างอิงหลักฐานจากบันทึกการเปิดตัวที่ได้รับอนุมัติ",
    "ms": "Atlas Output OUTPUT-SENTINEL-CP2 mewajibkan setiap item senarai semak yang dijana memetik bukti nota pelancaran yang diluluskan.",
}
ATLAS_OUTPUT_MARKER_TRANSLATED_SEGMENT_TEXT = {
    "hi": "Atlas Output निर्गम-शुद्धता पृथक्करण जाँचों के लिए OUTPUT-SENTINEL-CP2 चिह्न का उपयोग करता है।",
    "es": "Atlas Output usa el marcador OUTPUT-SENTINEL-CP2 para comprobaciones aisladas de corrección de salida.",
    "de": "Atlas Output verwendet die Markierung OUTPUT-SENTINEL-CP2 für isolierte Prüfungen der Ausgabekorrektheit.",
    "fr": "Atlas Output utilise le marqueur OUTPUT-SENTINEL-CP2 pour des vérifications isolées de la correction des sorties.",
    "pt-BR": "O Atlas Output usa o marcador OUTPUT-SENTINEL-CP2 para verificações isoladas de correção de saída.",
    "it": "Atlas Output usa il marcatore OUTPUT-SENTINEL-CP2 per verifiche isolate della correttezza dell'output.",
    "nl": "Atlas Output gebruikt de markering OUTPUT-SENTINEL-CP2 voor geïsoleerde controles van uitvoercorrectheid.",
    "pl": "Atlas Output używa znacznika OUTPUT-SENTINEL-CP2 do izolowanych kontroli poprawności wyników.",
    "uk": "Atlas Output використовує маркер OUTPUT-SENTINEL-CP2 для ізольованих перевірок правильності вихідних даних.",
    "ru": "Atlas Output использует маркер OUTPUT-SENTINEL-CP2 для изолированных проверок корректности вывода.",
    "zh-Hans": "Atlas Output 使用 OUTPUT-SENTINEL-CP2 标记进行输出正确性隔离检查。",
    "zh-Hant": "Atlas Output 使用 OUTPUT-SENTINEL-CP2 標記進行輸出正確性隔離檢查。",
    "ja": "Atlas Output は出力の正確性を切り分けて確認するために OUTPUT-SENTINEL-CP2 マーカーを使用します。",
    "ko": "Atlas Output은 출력 정확성을 분리해 확인하기 위해 OUTPUT-SENTINEL-CP2 표시자를 사용합니다.",
    "ar": "يستخدم Atlas Output العلامة OUTPUT-SENTINEL-CP2 لإجراء فحوصات معزولة لصحة المخرجات.",
    "arz": "يستخدم Atlas Output العلامة OUTPUT-SENTINEL-CP2 لإجراء فحوصات معزولة لصحة المخرجات.",
    "he": "Atlas Output משתמש בסמן OUTPUT-SENTINEL-CP2 לבדיקות מבודדות של תקינות הפלט.",
    "fa": "Atlas Output از نشانگر OUTPUT-SENTINEL-CP2 برای بررسی‌های جداگانه درستی خروجی استفاده می‌کند.",
    "tr": "Atlas Output, çıktı doğruluğunu yalıtılmış biçimde denetlemek için OUTPUT-SENTINEL-CP2 işaretleyicisini kullanır.",
    "vi": "Atlas Output dùng dấu hiệu OUTPUT-SENTINEL-CP2 cho các kiểm tra tách biệt về độ đúng của đầu ra.",
    "id": "Atlas Output menggunakan penanda OUTPUT-SENTINEL-CP2 untuk pemeriksaan terpisah atas kebenaran keluaran.",
    "fil": "Ginagamit ng Atlas Output ang panandang OUTPUT-SENTINEL-CP2 para sa nakahiwalay na mga pagsusuri ng kawastuhan ng output.",
    "th": "Atlas Output ใช้ตัวทำเครื่องหมาย OUTPUT-SENTINEL-CP2 สำหรับการตรวจสอบความถูกต้องของผลลัพธ์แบบแยกส่วน",
    "ms": "Atlas Output menggunakan penanda OUTPUT-SENTINEL-CP2 untuk semakan berasingan terhadap ketepatan output.",
}
ATLAS_OUTPUT_FIXTURE_TRANSLATIONS = {
    "Atlas Output OUTPUT-SENTINEL-CP2 is a fictional local checklist builder for launch rehearsals.": (
        ATLAS_OUTPUT_TRANSLATED_SEGMENT_TEXT
    ),
    "Atlas Output OUTPUT-SENTINEL-CP2 requires each generated checklist item to cite approved launch-note evidence.": (
        ATLAS_OUTPUT_CITATION_TRANSLATED_SEGMENT_TEXT
    ),
    "Atlas Output uses the marker OUTPUT-SENTINEL-CP2 for output-correctness isolation checks.": (
        ATLAS_OUTPUT_MARKER_TRANSLATED_SEGMENT_TEXT
    ),
}
HELIO_MEDIA_TRANSLATED_SEGMENT_TEXT = {
    "es": "Helio Media MEDIA-SENTINEL-CP4 es un estudio local ficticio de incorporación para equipos de operaciones de campo.",
}


@dataclass(frozen=True)
class TranslationProviderResult:
    provider: str
    provider_mode: str
    source_language: str
    target_language: str
    translated_text: str
    preserved_terms: list[str]


@dataclass(frozen=True)
class VoiceProviderResult:
    provider: str
    provider_mode: str
    requested_provider: str
    fallback_reason: str | None
    language: str
    artifact: DownloadableArtifact
    audio_artifact: DownloadableArtifact | None = None


@dataclass(frozen=True)
class MultilingualArtifacts:
    translated_script: DownloadableArtifact
    subtitles: DownloadableArtifact
    voice_manifest: DownloadableArtifact
    metadata: DownloadableArtifact
    voice_audio: DownloadableArtifact | None = None


@dataclass(frozen=True)
class MultilingualWalkthroughResult:
    multilingual_run_id: str
    request_checksum: str
    tenant_id: str
    project_id: str
    actor_id: str
    source_run_id: str
    source_language: str
    target_language: str
    status: str
    source_script_text: str
    source_text_checksum: str
    translated_script_text: str
    subtitles_text: str
    transcript_segments: tuple[MultilingualTranscriptSegment, ...]
    transcript_correctness: TranscriptCorrectness
    glossary_terms: list[str]
    preserved_terms: list[str]
    translation_provider: TranslationProviderResult
    voice: VoiceProviderResult
    artifacts: MultilingualArtifacts
    trace_id: str
    source_context_ref_count: int
    source_citation_count: int
    source_context_ref_ids: tuple[str, ...]
    source_citation_indexes: tuple[int, ...]
    source_claim_support_ids: tuple[str, ...]
    source_evaluation_id: str
    source_evaluation_checksum: str
    evaluation_status: EvaluationStatus


@dataclass
class Stage6IdempotencyRecord:
    idempotency_scope: str
    endpoint: str
    idempotency_key: str
    request_checksum: str
    status: Literal["PENDING", "RUNNING", "COMPLETED", "FAILED"]
    value: MultilingualWalkthroughResult | Stage6Error | None


@dataclass(frozen=True)
class TTSArtifactDeletionRecord:
    multilingual_run_id: str
    provider: str
    provider_history_item_id: str | None
    local_tombstone: bool
    provider_deletion_status: str
    requested_by: str
    reason: str


class TranslationProvider(Protocol):
    provider: str
    provider_mode: str

    def translate(
        self,
        *,
        source_text: str,
        source_language: str,
        target_language: str,
        glossary_terms: list[str],
    ) -> TranslationProviderResult:
        ...


class TTSProvider(Protocol):
    provider: str
    provider_mode: str

    def synthesize(
        self,
        *,
        text: str,
        language: str,
        requested_provider: str,
        fallback_reason: str | None,
    ) -> VoiceProviderResult:
        ...


class MockTranslationProvider:
    provider = "mock"
    provider_mode = "LOCAL"

    _REPLACEMENTS = {
        "es": (
            ("turns", "convierte"),
            ("approved", "aprobado"),
            ("into", "en"),
            ("grounded", "fundamentados"),
            ("walkthrough scripts", "guiones de recorrido"),
            ("keeps", "mantiene"),
            ("generated claims", "afirmaciones generadas"),
            ("tied to", "vinculadas a"),
            ("creates", "crea"),
            ("every", "cada"),
            ("must cite", "debe citar"),
        ),
        "fr": (
            ("turns", "transforme"),
            ("approved", "approuve"),
            ("into", "en"),
            ("grounded", "ancres"),
            ("walkthrough scripts", "scripts de presentation"),
            ("keeps", "garde"),
            ("generated claims", "affirmations generees"),
            ("tied to", "liees a"),
            ("creates", "cree"),
            ("every", "chaque"),
            ("must cite", "doit citer"),
        ),
        "hi": (
            ("turns", "बदलता है"),
            ("approved", "स्वीकृत"),
            ("into", "में"),
            ("grounded", "स्रोत-आधारित"),
            ("walkthrough scripts", "walkthrough scripts"),
            ("keeps", "रखता है"),
            ("generated claims", "generated claims"),
            ("tied to", "से जुड़ा"),
            ("creates", "बनाता है"),
            ("every", "हर"),
            ("must cite", "उद्धृत करना चाहिए"),
        ),
    }

    def translate(
        self,
        *,
        source_text: str,
        source_language: str,
        target_language: str,
        glossary_terms: list[str],
    ) -> TranslationProviderResult:
        if target_language == source_language:
            translated = source_text
        elif target_language in DEMO_TRANSLATED_SEGMENT_TEXT and citation_marker_sequence(source_text):
            translated = translate_demo_source_text(source_text=source_text, target_language=target_language)
            preserved_suffix = " ".join(term for term in glossary_terms if term in source_text and term not in translated)
            if preserved_suffix:
                translated = f"{translated} {preserved_suffix}"
        else:
            protected, placeholders = protect_terms(source_text, glossary_terms)
            translated = protected
            for source, target in self._REPLACEMENTS.get(target_language, ()):
                translated = re.sub(rf"\b{re.escape(source)}\b", target, translated, flags=re.IGNORECASE)
            if translated == protected and target_language in DEMO_TRANSLATED_SEGMENT_TEXT:
                translated = translate_demo_source_text(source_text=restore_terms(protected, placeholders), target_language=target_language)
            translated = restore_terms(translated, placeholders)
        return TranslationProviderResult(
            provider=self.provider,
            provider_mode=self.provider_mode,
            source_language=source_language,
            target_language=target_language,
            translated_text=translated,
            preserved_terms=[term for term in glossary_terms if term in translated],
        )


class MockTTSProvider:
    provider = "mock"
    provider_mode = "LOCAL"

    def synthesize(
        self,
        *,
        text: str,
        language: str,
        requested_provider: str,
        fallback_reason: str | None,
    ) -> VoiceProviderResult:
        manifest = {
            "provider": self.provider,
            "providerMode": self.provider_mode,
            "language": language,
            "languageDisplayName": language_display_name(language),
            "textChecksum": checksum_text(text),
            "durationSecondsEstimate": estimate_duration_seconds(text),
            "mockAudioProfile": mock_audio_profile(estimate_duration_seconds(text)),
            "disclosure": "Mock local TTS placeholder. No cloned voice or paid provider was used.",
        }
        return VoiceProviderResult(
            provider=self.provider,
            provider_mode=self.provider_mode,
            requested_provider=requested_provider,
            fallback_reason=fallback_reason,
            language=language,
            artifact=artifact_from_text(
                file_name=f"voice-manifest-{language}.json",
                mime_type="application/json",
                text=json.dumps(manifest, sort_keys=True),
            ),
        )


class Stage6Service:
    def __init__(
        self,
        *,
        translation_provider: TranslationProvider | None = None,
        tts_provider: TTSProvider | None = None,
        external_tts_provider: ElevenLabsTTSProvider | None = None,
        state_path: Path | None = None,
    ) -> None:
        self.translation_provider = translation_provider or MockTranslationProvider()
        self.tts_provider = tts_provider or MockTTSProvider()
        self.external_tts_provider = external_tts_provider
        self.state_path = state_path
        self.multilingual_runs: dict[str, MultilingualWalkthroughResult] = {}
        self.tts_deletions: dict[str, TTSArtifactDeletionRecord] = {}
        self.request_dedupe_index: dict[tuple[str, str], str] = {}
        self.idempotency_records: dict[tuple[str, str, str], Stage6IdempotencyRecord] = {}
        self._operation_lock = threading.Lock()
        self._run_counter = 0
        self._restore()

    def reset(self) -> None:
        with self._operation_lock:
            self.translation_provider = MockTranslationProvider()
            self.tts_provider = MockTTSProvider()
            self.external_tts_provider = None
            self._clear_runtime_state()
            self._persist_locked()

    def _clear_runtime_state(self) -> None:
        self.multilingual_runs.clear()
        self.tts_deletions.clear()
        self.request_dedupe_index.clear()
        self.idempotency_records.clear()
        self._run_counter = 0

    def _restore(self) -> None:
        payload = load_state(self.state_path)
        if payload is None:
            return
        try:
            schema = payload.get("schema")
            if schema not in {"stage6-local-state-v1", "stage6-local-state-v2"}:
                raise ValueError("Stage 6 state schema mismatch.")
            counters = payload.get("counters", {})
            run_counter = 0
            if isinstance(counters, dict):
                run_counter = int(counters.get("run", 0))
            restored_runs: dict[str, MultilingualWalkthroughResult] = {}
            for row in payload.get("multilingualRuns", []):
                if not isinstance(row, dict):
                    continue
                try:
                    result = multilingual_result_from_dict(cast(dict[str, Any], row))
                except (KeyError, TypeError, ValueError, Stage6Error) as exc:
                    LOGGER.warning(
                        "Skipping incompatible Stage 6 multilingual run at %s: %s",
                        self.state_path,
                        type(exc).__name__,
                    )
                    continue
                restored_runs[result.multilingual_run_id] = result
            restored_dedupe_index: dict[tuple[str, str], str] = {}
            for row in payload.get("idempotencyRecords", []):
                if not isinstance(row, dict):
                    continue
                if row.get("status") in {"PENDING", "RUNNING"}:
                    continue
                try:
                    record = stage6_idempotency_record_from_dict(row)
                except (KeyError, TypeError, ValueError, Stage6Error) as exc:
                    LOGGER.warning(
                        "Skipping incompatible Stage 6 idempotency record at %s: %s",
                        self.state_path,
                        type(exc).__name__,
                    )
                    continue
                if record.status == "COMPLETED":
                    if not isinstance(record.value, MultilingualWalkthroughResult):
                        continue
                    result = record.value
                    if record.request_checksum != result.request_checksum:
                        continue
                    existing_result = restored_runs.get(result.multilingual_run_id)
                    if existing_result is not None and existing_result != result:
                        continue
                    dedupe_key = (record.idempotency_scope, record.request_checksum)
                    existing_run_id = restored_dedupe_index.get(dedupe_key)
                    if existing_run_id is not None and existing_run_id != result.multilingual_run_id:
                        continue
                    restored_runs[result.multilingual_run_id] = result
                    restored_dedupe_index[dedupe_key] = result.multilingual_run_id
                key = (record.idempotency_scope, record.endpoint, record.idempotency_key)
                self.idempotency_records[key] = record
            for row in payload.get("requestDedupeIndex", []):
                if not isinstance(row, dict):
                    continue
                try:
                    scope = str(row["idempotency_scope"])
                    request_checksum = str(row["request_checksum"])
                    multilingual_run_id = str(row["multilingual_run_id"])
                except KeyError:
                    continue
                restored_result: MultilingualWalkthroughResult | None = restored_runs.get(multilingual_run_id)
                if restored_result is None or restored_result.request_checksum != request_checksum:
                    continue
                try:
                    validate_stage6_scope(
                        idempotency_scope=scope,
                        tenant_id=restored_result.tenant_id,
                        project_id=restored_result.project_id,
                        actor_id=restored_result.actor_id,
                        source_run_id=restored_result.source_run_id,
                    )
                except Stage6Error:
                    continue
                dedupe_key = (scope, request_checksum)
                existing_run_id = restored_dedupe_index.get(dedupe_key)
                if existing_run_id is not None and existing_run_id != multilingual_run_id:
                    continue
                restored_dedupe_index[dedupe_key] = multilingual_run_id
            restored_tts_deletions: dict[str, TTSArtifactDeletionRecord] = {}
            for row in payload.get("ttsDeletions", []):
                if not isinstance(row, dict):
                    continue
                try:
                    deletion = tts_artifact_deletion_record_from_dict(cast(dict[str, Any], row))
                except (KeyError, TypeError, ValueError, Stage6Error) as exc:
                    LOGGER.warning(
                        "Skipping incompatible Stage 6 TTS deletion record at %s: %s",
                        self.state_path,
                        type(exc).__name__,
                    )
                    continue
                restored_tts_deletions[deletion.multilingual_run_id] = deletion
            self.multilingual_runs = {
                run_id: result
                for run_id, result in restored_runs.items()
                if run_id in restored_dedupe_index.values()
                or any(
                    isinstance(record.value, MultilingualWalkthroughResult)
                    and record.value.multilingual_run_id == run_id
                    for record in self.idempotency_records.values()
                )
            }
            self.request_dedupe_index = {
                key: run_id for key, run_id in restored_dedupe_index.items() if run_id in self.multilingual_runs
            }
            self.tts_deletions = {
                run_id: deletion
                for run_id, deletion in restored_tts_deletions.items()
                if run_id in self.multilingual_runs
            }
            self._run_counter = max(
                run_counter,
                max_multilingual_run_suffix(self.idempotency_records),
                max_multilingual_run_identifier(self.multilingual_runs),
            )
        except (KeyError, TypeError, ValueError, Stage6Error) as exc:
            LOGGER.warning(
                "Ignoring incompatible Stage 6 local state snapshot at %s: %s",
                self.state_path,
                type(exc).__name__,
            )
            self._clear_runtime_state()

    def _runtime_snapshot_locked(self) -> dict[str, Any]:
        return {
            "multilingualRuns": self.multilingual_runs.copy(),
            "requestDedupeIndex": self.request_dedupe_index.copy(),
            "idempotencyRecords": self.idempotency_records.copy(),
            "runCounter": self._run_counter,
        }

    def _restore_failed_operation_locked(
        self,
        snapshot: dict[str, Any] | None,
        *,
        record_key: tuple[str, str, str] | None,
        result: MultilingualWalkthroughResult | None,
    ) -> None:
        if snapshot is None:
            return
        current_record = self.idempotency_records.get(record_key) if record_key is not None else None
        dedupe_key = (
            (current_record.idempotency_scope, current_record.request_checksum) if current_record is not None else None
        )
        if record_key is not None:
            prior_record = snapshot["idempotencyRecords"].get(record_key)
            if prior_record is None:
                self.idempotency_records.pop(record_key, None)
            else:
                self.idempotency_records[record_key] = prior_record
        if result is not None:
            self.multilingual_runs.pop(result.multilingual_run_id, None)
            for key, record in list(self.idempotency_records.items()):
                if (
                    key != record_key
                    and isinstance(record.value, MultilingualWalkthroughResult)
                    and record.value.multilingual_run_id == result.multilingual_run_id
                ):
                    self.idempotency_records.pop(key, None)
            for dedupe_index_key, run_id in list(self.request_dedupe_index.items()):
                if run_id == result.multilingual_run_id:
                    self.request_dedupe_index.pop(dedupe_index_key, None)
        if dedupe_key is not None:
            prior_run_id = snapshot["requestDedupeIndex"].get(dedupe_key)
            if prior_run_id is None:
                self.request_dedupe_index.pop(dedupe_key, None)
            else:
                self.request_dedupe_index[dedupe_key] = prior_run_id
        for run_id, stored_result in snapshot["multilingualRuns"].items():
            if run_id in self.request_dedupe_index.values() or any(
                isinstance(record.value, MultilingualWalkthroughResult)
                and record.value.multilingual_run_id == run_id
                for record in self.idempotency_records.values()
            ):
                self.multilingual_runs[run_id] = stored_result
        self._run_counter = max(
            int(snapshot["runCounter"]),
            max_multilingual_run_suffix(self.idempotency_records),
            max_multilingual_run_identifier(self.multilingual_runs),
        )

    def _persist_locked(self) -> None:
        write_state(
            self.state_path,
            {
                "schema": "stage6-local-state-v2",
                "multilingualRuns": [multilingual_result_to_dict(result) for result in self.multilingual_runs.values()],
                "requestDedupeIndex": [
                    {
                        "idempotency_scope": scope,
                        "request_checksum": request_checksum,
                        "multilingual_run_id": multilingual_run_id,
                    }
                    for (scope, request_checksum), multilingual_run_id in self.request_dedupe_index.items()
                ],
                "idempotencyRecords": [
                    stage6_idempotency_record_to_dict(record)
                    for record in self.idempotency_records.values()
                    if record.status not in {"PENDING", "RUNNING"}
                ],
                "ttsDeletions": [
                    tts_artifact_deletion_record_to_dict(record) for record in self.tts_deletions.values()
                ],
                "counters": {"run": self._run_counter},
            },
        )

    def generate_multilingual_walkthrough(
        self,
        *,
        source_script: str,
        target_language: str,
        glossary_terms: Iterable[str] = (),
        source_language: str = "en",
        tenant_id: str = "tenant",
        project_id: str = "project",
        actor_id: str = "user",
        requested_voice_provider: str = "mock",
        source_run_id: str = "local_source_run",
        trace_id: str = "local_trace",
        source_context_ref_count: int = 0,
        source_citation_count: int = 0,
        source_context_ref_ids: tuple[str, ...] | None = None,
        source_citation_indexes: tuple[int, ...] | None = None,
        source_claim_support_ids: tuple[str, ...] | None = None,
        source_evaluation_id: str = "eval_local",
        source_evaluation_checksum: str = "",
        evaluation_status: str = "UNKNOWN",
        idempotency_scope: str | None = None,
        idempotency_key: str | None = None,
    ) -> MultilingualWalkthroughResult:
        raw_glossary_terms = list(glossary_terms)
        normalized_tenant_id = validate_checksum_component(tenant_id, field_name="tenant identifier")
        normalized_project_id = validate_checksum_component(project_id, field_name="project identifier")
        normalized_actor_id = validate_checksum_component(actor_id, field_name="actor identifier")
        normalized_source_run_id = validate_checksum_component(source_run_id, field_name="source run identifier")
        normalized_trace_id = validate_checksum_component(trace_id, field_name="source trace identifier")
        source_text = source_script.strip()
        source_text_checksum = checksum_text(source_text)
        raw_source_context_ref_ids = tuple(source_context_ref_ids or ())
        raw_source_citation_indexes = tuple(source_citation_indexes or ())
        raw_source_claim_support_ids = tuple(source_claim_support_ids or ())
        raw_source_evaluation_id = source_evaluation_id.strip() or "eval_local"
        raw_evaluation_status = evaluation_status.strip().upper() or "UNKNOWN"
        raw_source_evaluation_checksum = source_evaluation_checksum.strip() or build_source_evaluation_checksum(
            source_evaluation_id=raw_source_evaluation_id,
            source_run_id=normalized_source_run_id,
            trace_id=normalized_trace_id,
            evaluation_status=cast(EvaluationStatus, raw_evaluation_status),
            source_context_ref_ids=raw_source_context_ref_ids,
            source_context_ref_count=source_context_ref_count,
            source_citation_indexes=raw_source_citation_indexes,
            source_citation_count=source_citation_count,
        )
        normalized_source_language = normalize_language_tag(source_language)
        normalized_target_language = normalize_language_tag(target_language)
        normalized_terms = normalize_glossary_terms(raw_glossary_terms)
        normalized_requested_voice_provider = validate_provider_id(
            requested_voice_provider or "mock",
            field_name="requested voice provider",
        )
        normalized_evaluation_status = validate_evaluation_status(raw_evaluation_status)
        normalized_evaluation_id = normalize_evaluation_id(raw_source_evaluation_id)
        request_checksum = build_multilingual_request_checksum(
            source_script=source_text,
            source_language=normalized_source_language,
            target_language=normalized_target_language,
            requested_voice_provider=normalized_requested_voice_provider,
            glossary_terms=normalized_terms,
            tenant_id=normalized_tenant_id,
            project_id=normalized_project_id,
            actor_id=normalized_actor_id,
            source_run_id=normalized_source_run_id,
            trace_id=normalized_trace_id,
            source_context_ref_count=source_context_ref_count,
            source_citation_count=source_citation_count,
            source_context_ref_ids=raw_source_context_ref_ids,
            source_citation_indexes=raw_source_citation_indexes,
            source_claim_support_ids=raw_source_claim_support_ids,
            source_evaluation_id=normalized_evaluation_id,
            source_evaluation_checksum=raw_source_evaluation_checksum,
            evaluation_status=normalized_evaluation_status,
        )
        endpoint = "POST /api/v1/projects/{project_id}/walkthrough-runs/{run_id}/multilingual-runs"
        if idempotency_scope and idempotency_key:
            validate_stage6_scope(
                idempotency_scope=idempotency_scope,
                tenant_id=normalized_tenant_id,
                project_id=normalized_project_id,
                actor_id=normalized_actor_id,
                source_run_id=normalized_source_run_id,
            )
        record_key: tuple[str, str, str] | None = None
        snapshot: dict[str, Any] | None = None
        result: MultilingualWalkthroughResult | None = None

        if idempotency_scope and idempotency_key:
            record_key = (idempotency_scope, endpoint, idempotency_key)
            with self._operation_lock:
                existing = self.idempotency_records.get(record_key)
                if existing is not None:
                    if existing.request_checksum != request_checksum:
                        raise Stage6Error(
                            409,
                            "IDEMPOTENCY_CONFLICT",
                            "Idempotency key was reused with a different request.",
                        )
                    if existing.status in {"PENDING", "RUNNING"}:
                        raise Stage6Error(
                            409,
                            "IDEMPOTENCY_IN_PROGRESS",
                            "Idempotency key is already in progress.",
                        )
                    if existing.status == "FAILED":
                        raise cast(Stage6Error, existing.value)
                    return cast(MultilingualWalkthroughResult, existing.value)
                if self._idempotency_count_for_scope(idempotency_scope) >= MAX_IDEMPOTENCY_RECORDS_PER_SCOPE:
                    raise Stage6Error(
                        429,
                        "RESOURCE_LIMIT_EXCEEDED",
                        "Idempotency record limit exceeded for this Stage 6 scope.",
                    )
                deduped = self._replay_deduped_result(
                    idempotency_scope=idempotency_scope,
                    request_checksum=request_checksum,
                )
                if deduped is not None:
                    self.idempotency_records[record_key] = Stage6IdempotencyRecord(
                        idempotency_scope=idempotency_scope,
                        endpoint=endpoint,
                        idempotency_key=idempotency_key,
                        request_checksum=request_checksum,
                        status="COMPLETED",
                        value=deduped,
                    )
                    self._persist_locked()
                    return deduped
                snapshot = self._runtime_snapshot_locked()
                self.idempotency_records[record_key] = Stage6IdempotencyRecord(
                    idempotency_scope=idempotency_scope,
                    endpoint=endpoint,
                    idempotency_key=idempotency_key,
                    request_checksum=request_checksum,
                    status="RUNNING",
                    value=None,
                )
                self._persist_locked()

        try:
            if any(contains_secret_like_content(term) for term in normalized_terms):
                raise Stage6Error(422, "SECRET_LIKE_CONTENT", "Glossary terms contain secret-like content.")
            if not source_text:
                raise Stage6Error(422, "VALIDATION_ERROR", "Source English script is required.")
            if len(source_text) > MAX_SOURCE_SCRIPT_CHARS:
                raise Stage6Error(413, "SOURCE_SCRIPT_TOO_LARGE", "Source English script exceeds the Stage 6 limit.")
            normalized_context_ref_ids = normalize_evidence_ids(
                raw_source_context_ref_ids,
                count=source_context_ref_count,
                prefix="ctx_",
                field_name="source context reference identifiers",
            )
            normalized_citation_indexes = normalize_citation_indexes(
                raw_source_citation_indexes,
                count=source_citation_count,
            )
            normalized_claim_support_ids = normalize_evidence_ids(
                raw_source_claim_support_ids,
                count=source_citation_count,
                prefix="claimsup_",
                field_name="source claim-support identifiers",
            )
            normalized_evaluation_checksum = validate_source_evaluation_checksum(
                source_evaluation_checksum=raw_source_evaluation_checksum,
                source_evaluation_id=normalized_evaluation_id,
                source_run_id=normalized_source_run_id,
                trace_id=normalized_trace_id,
                evaluation_status=normalized_evaluation_status,
                source_context_ref_ids=normalized_context_ref_ids,
                source_context_ref_count=source_context_ref_count,
                source_citation_indexes=normalized_citation_indexes,
                source_citation_count=source_citation_count,
            )
            validate_multilingual_source_evidence(
                source_text=source_text,
                evaluation_status=normalized_evaluation_status,
                source_evaluation_checksum_supplied=bool(source_evaluation_checksum.strip()),
                source_context_ref_count=source_context_ref_count,
                source_citation_count=source_citation_count,
                source_context_ref_ids=normalized_context_ref_ids,
                source_citation_indexes=normalized_citation_indexes,
                source_claim_support_ids=normalized_claim_support_ids,
            )
        except Stage6Error as exc:
            if record_key is not None:
                self._store_idempotent_failure(record_key, exc, snapshot)
            raise

        try:
            result = self._create_multilingual_walkthrough(
                source_text=source_text,
                normalized_source_language=normalized_source_language,
                normalized_target_language=normalized_target_language,
                normalized_terms=normalized_terms,
                requested_voice_provider=requested_voice_provider,
                request_checksum=request_checksum,
                tenant_id=normalized_tenant_id,
                project_id=normalized_project_id,
                actor_id=normalized_actor_id,
                source_run_id=normalized_source_run_id,
                trace_id=normalized_trace_id,
                source_text_checksum=source_text_checksum,
                source_context_ref_count=source_context_ref_count,
                source_citation_count=source_citation_count,
                source_context_ref_ids=normalized_context_ref_ids,
                source_citation_indexes=normalized_citation_indexes,
                source_claim_support_ids=normalized_claim_support_ids,
                source_evaluation_id=normalized_evaluation_id,
                source_evaluation_checksum=normalized_evaluation_checksum,
                evaluation_status=normalized_evaluation_status,
                source_evaluation_checksum_supplied=bool(source_evaluation_checksum.strip()),
            )
        except Stage6Error as exc:
            if record_key is not None:
                self._store_idempotent_failure(record_key, exc, snapshot)
            raise
        except OSError:
            if snapshot is not None:
                with self._operation_lock:
                    self._restore_failed_operation_locked(snapshot, record_key=record_key, result=result)
            raise
        except Exception:
            if record_key is not None:
                with self._operation_lock:
                    self._restore_failed_operation_locked(snapshot, record_key=record_key, result=result)
                    self._persist_locked()
            raise

        assert result is not None
        if record_key is not None:
            with self._operation_lock:
                record = self.idempotency_records[record_key]
                record.status = "COMPLETED"
                record.value = result
                self.multilingual_runs[result.multilingual_run_id] = result
                self.request_dedupe_index[(record.idempotency_scope, record.request_checksum)] = result.multilingual_run_id
                try:
                    self._persist_locked()
                except OSError:
                    self._restore_failed_operation_locked(snapshot, record_key=record_key, result=result)
                    raise
        else:
            with self._operation_lock:
                self.multilingual_runs[result.multilingual_run_id] = result
                self._persist_locked()
        return result

    def _store_idempotent_failure(
        self,
        record_key: tuple[str, str, str],
        error: Stage6Error,
        snapshot: dict[str, Any] | None,
    ) -> None:
        with self._operation_lock:
            record = self.idempotency_records[record_key]
            record.status = "FAILED"
            record.value = error
            try:
                self._persist_locked()
            except OSError:
                self._restore_failed_operation_locked(snapshot, record_key=record_key, result=None)
                raise error

    def _create_multilingual_walkthrough(
        self,
        *,
        source_text: str,
        normalized_source_language: str,
        normalized_target_language: str,
        normalized_terms: list[str],
        requested_voice_provider: str,
        request_checksum: str,
        tenant_id: str,
        project_id: str,
        actor_id: str,
        source_run_id: str,
        trace_id: str,
        source_text_checksum: str,
        source_context_ref_count: int,
        source_citation_count: int,
        source_context_ref_ids: tuple[str, ...],
        source_citation_indexes: tuple[int, ...],
        source_claim_support_ids: tuple[str, ...],
        source_evaluation_id: str,
        source_evaluation_checksum: str,
        evaluation_status: EvaluationStatus,
        source_evaluation_checksum_supplied: bool,
    ) -> MultilingualWalkthroughResult:
        translation = self.translation_provider.translate(
            source_text=source_text,
            source_language=normalized_source_language,
            target_language=normalized_target_language,
            glossary_terms=normalized_terms,
        )
        validated_text, preserved_terms, citation_count = validate_translation_output(
            source_text=source_text,
            translated_text=translation.translated_text,
            glossary_terms=normalized_terms,
        )
        if citation_count != source_citation_count:
            raise Stage6Error(422, "PROVIDER_OUTPUT_INVALID", "Translated output citation count is inconsistent.")
        translation = TranslationProviderResult(
            provider=validate_provider_id(translation.provider, field_name="translation provider"),
            provider_mode=validate_local_provider_mode(
                translation.provider_mode,
                field_name="translation provider mode",
            ),
            source_language=normalized_source_language,
            target_language=normalized_target_language,
            translated_text=validated_text,
            preserved_terms=preserved_terms,
        )
        transcript_segments = build_multilingual_transcript_segments(
            source_text=source_text,
            target_language=normalized_target_language,
            source_run_id=source_run_id,
            source_evaluation_id=source_evaluation_id,
            source_context_ref_ids=source_context_ref_ids,
            source_claim_support_ids=source_claim_support_ids,
        )
        transcript_correctness = validate_multilingual_transcript_correctness(
            target_language=normalized_target_language,
            source_text=source_text,
            segments=transcript_segments,
            source_run_id=source_run_id,
            evaluation_id=source_evaluation_id,
            context_ref_ids=source_context_ref_ids,
            citation_indexes=source_citation_indexes,
            claim_support_ids=source_claim_support_ids,
        )
        validate_translated_script_matches_transcript(
            target_language=normalized_target_language,
            source_text=source_text,
            translated_script_text=translation.translated_text,
            transcript_segments=transcript_segments,
        )
        if normalized_target_language != "en" and translation.translated_text == source_text:
            raise Stage6Error(422, "TRANSCRIPT_CORRECTNESS_FAILED", "Provider returned an English fallback.")
        subtitles_text = generate_subtitles(
            script_text=translation.translated_text,
            language=normalized_target_language,
        )
        provider_name, fallback_reason = resolve_voice_provider(requested_voice_provider)
        if provider_name == "elevenlabs" and fallback_reason is None:
            voice = self._synthesize_external_tts(
                text=translation.translated_text,
                language=normalized_target_language,
                provider_name=provider_name,
                request_checksum=request_checksum,
                actor_id=actor_id,
                source_run_id=source_run_id,
                trace_id=trace_id,
                source_context_ref_count=source_context_ref_count,
                source_context_ref_ids=source_context_ref_ids,
                source_citation_count=source_citation_count,
                source_citation_indexes=source_citation_indexes,
                source_claim_support_ids=source_claim_support_ids,
                source_evaluation_id=source_evaluation_id,
                source_evaluation_checksum=source_evaluation_checksum,
                evaluation_status=evaluation_status,
                source_evaluation_checksum_supplied=source_evaluation_checksum_supplied,
            )
        else:
            voice = self.tts_provider.synthesize(
                text=translation.translated_text,
                language=normalized_target_language,
                requested_provider=provider_name,
                fallback_reason=fallback_reason,
            )
            voice = VoiceProviderResult(
                provider=validate_provider_id(voice.provider, field_name="voice provider"),
                provider_mode=validate_local_provider_mode(voice.provider_mode, field_name="voice provider mode"),
                requested_provider=provider_name,
                fallback_reason=voice.fallback_reason,
                language=normalized_target_language,
                artifact=validate_voice_manifest_artifact(voice.artifact),
                audio_artifact=None,
            )
        with self._operation_lock:
            self._run_counter += 1
            multilingual_run_id = f"mlrun_{self._run_counter:06d}"
        script_artifact = validate_downloadable_artifact(
            artifact_from_text(
                file_name=f"{source_run_id}-{normalized_target_language}-script.md",
                mime_type="text/markdown",
                text=render_translated_script_artifact_text(
                    target_language=normalized_target_language,
                    transcript_segments=transcript_segments,
                    transcript_correctness=transcript_correctness,
                ),
            ),
            expected_mime_type="text/markdown",
            expected_extension=".md",
        )
        subtitle_artifact = validate_downloadable_artifact(
            artifact_from_text(
                file_name=f"{source_run_id}-{normalized_target_language}.srt",
                mime_type="application/x-subrip",
                text=subtitles_text,
            ),
            expected_mime_type="application/x-subrip",
            expected_extension=".srt",
        )
        metadata_text = build_stage6_metadata_text(
            multilingual_run_id=multilingual_run_id,
            request_checksum=request_checksum,
            tenant_id=tenant_id,
            project_id=project_id,
            actor_id=actor_id,
            source_run_id=source_run_id,
            trace_id=trace_id,
            source_language=normalized_source_language,
            target_language=normalized_target_language,
            source_text_checksum=source_text_checksum,
            source_context_ref_count=source_context_ref_count,
            source_context_ref_ids=source_context_ref_ids,
            source_citation_count=source_citation_count,
            source_citation_indexes=source_citation_indexes,
            source_claim_support_ids=source_claim_support_ids,
            source_evaluation_id=source_evaluation_id,
            source_evaluation_checksum=source_evaluation_checksum,
            evaluation_status=evaluation_status,
            glossary_terms=normalized_terms,
            preserved_terms=translation.preserved_terms,
            source_script_text=source_text,
            translated_script_text=translation.translated_text,
            transcript_segments=transcript_segments,
            transcript_correctness=transcript_correctness,
            translation_provider=translation,
            voice=voice,
            translated_script_artifact=script_artifact,
            subtitles_artifact=subtitle_artifact,
        )
        metadata_artifact = validate_downloadable_artifact(
            artifact_from_text(
                file_name=f"{source_run_id}-{normalized_target_language}-metadata.json",
                mime_type="application/json",
                text=metadata_text,
            ),
            expected_mime_type="application/json",
            expected_extension=".json",
        )
        return MultilingualWalkthroughResult(
            multilingual_run_id=multilingual_run_id,
            request_checksum=request_checksum,
            tenant_id=tenant_id,
            project_id=project_id,
            actor_id=actor_id,
            source_run_id=source_run_id,
            source_language=normalized_source_language,
            target_language=normalized_target_language,
            status="COMPLETED",
            source_script_text=source_text,
            source_text_checksum=source_text_checksum,
            translated_script_text=translation.translated_text,
            subtitles_text=subtitles_text,
            transcript_segments=transcript_segments,
            transcript_correctness=transcript_correctness,
            glossary_terms=normalized_terms,
            preserved_terms=translation.preserved_terms,
            translation_provider=translation,
            voice=voice,
            artifacts=MultilingualArtifacts(
                translated_script=script_artifact,
                subtitles=subtitle_artifact,
                voice_manifest=voice.artifact,
                metadata=metadata_artifact,
                voice_audio=voice.audio_artifact,
            ),
            trace_id=trace_id,
            source_context_ref_count=source_context_ref_count,
            source_citation_count=source_citation_count,
            source_context_ref_ids=source_context_ref_ids,
            source_citation_indexes=source_citation_indexes,
            source_claim_support_ids=source_claim_support_ids,
            source_evaluation_id=source_evaluation_id,
            source_evaluation_checksum=source_evaluation_checksum,
            evaluation_status=evaluation_status,
        )

    def _synthesize_external_tts(
        self,
        *,
        text: str,
        language: str,
        provider_name: str,
        request_checksum: str,
        actor_id: str,
        source_run_id: str,
        trace_id: str,
        source_context_ref_count: int,
        source_context_ref_ids: tuple[str, ...],
        source_citation_count: int,
        source_citation_indexes: tuple[int, ...],
        source_claim_support_ids: tuple[str, ...],
        source_evaluation_id: str,
        source_evaluation_checksum: str,
        evaluation_status: EvaluationStatus,
        source_evaluation_checksum_supplied: bool,
    ) -> VoiceProviderResult:
        if self.external_tts_provider is None:
            raise Stage6Error(403, "TTS_PROVIDER_DISABLED", "TTS provider is disabled.")
        if (
            evaluation_status != "PASSED"
            or not source_evaluation_checksum_supplied
            or source_context_ref_count <= 0
            or source_citation_count <= 0
            or not source_context_ref_ids
            or not source_citation_indexes
            or not source_claim_support_ids
        ):
            raise Stage6Error(
                422,
                "TTS_SOURCE_EVALUATION_REQUIRED",
                "Real TTS requires passed source evaluation and citation evidence.",
            )
        try:
            external_result = self.external_tts_provider.synthesize(
                text=text,
                language=language,
                request_id=request_checksum,
                trace_id=trace_id,
            )
        except TTSProviderError as exc:
            raise Stage6Error(exc.status_code, exc.code, exc.message) from exc
        audio_artifact = validate_audio_artifact(
            artifact_from_bytes(
                file_name=f"{source_run_id}-{language}-voice{SUPPORTED_AUDIO_MIME_TYPES[external_result.mime_type]}",
                mime_type=external_result.mime_type,
                content=external_result.audio_bytes,
            )
        )
        manifest_text = build_tts_manifest_text(
            provider_result=external_result,
            requested_provider=provider_name,
            language=language,
            text=text,
            actor_id=actor_id,
            source_run_id=source_run_id,
            trace_id=trace_id,
            source_context_ref_count=source_context_ref_count,
            source_context_ref_ids=source_context_ref_ids,
            source_citation_count=source_citation_count,
            source_citation_indexes=source_citation_indexes,
            source_claim_support_ids=source_claim_support_ids,
            source_evaluation_id=source_evaluation_id,
            source_evaluation_checksum=source_evaluation_checksum,
            evaluation_status=evaluation_status,
            audio_artifact=audio_artifact,
        )
        manifest_artifact = validate_tts_manifest_artifact(
            artifact_from_text(
                file_name=f"{source_run_id}-{language}-tts-manifest.json",
                mime_type="application/json",
                text=manifest_text,
            )
        )
        return VoiceProviderResult(
            provider=validate_provider_id(external_result.provider, field_name="voice provider"),
            provider_mode=validate_provider_mode(external_result.provider_mode),
            requested_provider=provider_name,
            fallback_reason=None,
            language=language,
            artifact=manifest_artifact,
            audio_artifact=audio_artifact,
        )

    def _idempotency_count_for_scope(self, idempotency_scope: str) -> int:
        return sum(record.idempotency_scope == idempotency_scope for record in self.idempotency_records.values())

    def _replay_deduped_result(
        self,
        *,
        idempotency_scope: str,
        request_checksum: str,
    ) -> MultilingualWalkthroughResult | None:
        multilingual_run_id = self.request_dedupe_index.get((idempotency_scope, request_checksum))
        if multilingual_run_id is None:
            return None
        return self.multilingual_runs.get(multilingual_run_id)

    def delete_tts_artifacts(
        self,
        *,
        multilingual_run_id: str,
        requested_by: str,
        reason: str,
    ) -> TTSArtifactDeletionRecord:
        normalized_requested_by = validate_checksum_component(requested_by, field_name="TTS deletion requester")
        normalized_reason = " ".join(reason.strip().split())
        if not normalized_reason:
            raise Stage6Error(422, "VALIDATION_ERROR", "TTS deletion reason is required.")
        with self._operation_lock:
            result = self.multilingual_runs.get(multilingual_run_id)
            if result is None:
                raise Stage6Error(404, "NOT_FOUND", "Multilingual run was not found.")
            manifest = json.loads(artifact_text(result.voice.artifact))
            provider_history_item_id = (
                str(manifest["providerHistoryItemId"]) if manifest.get("providerHistoryItemId") is not None else None
            )
            provider_deletion_status = (
                "PENDING_PROVIDER_DELETE"
                if result.voice.provider_mode == "OPTIONAL_EXTERNAL" and provider_history_item_id is not None
                else "NOT_APPLICABLE"
            )
            updated_voice = replace(result.voice, audio_artifact=None)
            updated_artifacts = replace(result.artifacts, voice_audio=None)
            updated_result = replace(
                result,
                voice=updated_voice,
                artifacts=updated_artifacts,
            )
            self.multilingual_runs[multilingual_run_id] = updated_result
            for record in self.idempotency_records.values():
                if (
                    isinstance(record.value, MultilingualWalkthroughResult)
                    and record.value.multilingual_run_id == multilingual_run_id
                ):
                    record.value = updated_result
            deletion = TTSArtifactDeletionRecord(
                multilingual_run_id=multilingual_run_id,
                provider=result.voice.provider,
                provider_history_item_id=provider_history_item_id,
                local_tombstone=True,
                provider_deletion_status=provider_deletion_status,
                requested_by=normalized_requested_by,
                reason=normalized_reason,
            )
            self.tts_deletions[multilingual_run_id] = deletion
            self._persist_locked()
            return deletion


def tts_artifact_deletion_record_to_dict(record: TTSArtifactDeletionRecord) -> dict[str, Any]:
    return asdict(record)


def tts_artifact_deletion_record_from_dict(row: dict[str, Any]) -> TTSArtifactDeletionRecord:
    multilingual_run_id = validate_checksum_component(
        str(row["multilingual_run_id"]),
        field_name="TTS deletion multilingual run identifier",
    )
    provider = validate_provider_id(str(row["provider"]), field_name="TTS deletion provider")
    provider_history_item_id = row.get("provider_history_item_id")
    normalized_provider_history_item_id = (
        validate_checksum_component(str(provider_history_item_id), field_name="TTS provider history item identifier")
        if provider_history_item_id is not None
        else None
    )
    provider_deletion_status = str(row["provider_deletion_status"])
    if provider_deletion_status not in {"PENDING_PROVIDER_DELETE", "NOT_APPLICABLE"}:
        raise ValueError("Unsupported TTS provider deletion status.")
    return TTSArtifactDeletionRecord(
        multilingual_run_id=multilingual_run_id,
        provider=provider,
        provider_history_item_id=normalized_provider_history_item_id,
        local_tombstone=bool(row["local_tombstone"]),
        provider_deletion_status=provider_deletion_status,
        requested_by=validate_checksum_component(str(row["requested_by"]), field_name="TTS deletion requester"),
        reason=" ".join(str(row["reason"]).strip().split()),
    )


def stage6_idempotency_record_to_dict(record: Stage6IdempotencyRecord) -> dict[str, Any]:
    row: dict[str, Any] = {
        "idempotency_scope": record.idempotency_scope,
        "endpoint": record.endpoint,
        "idempotency_key": record.idempotency_key,
        "request_checksum": record.request_checksum,
        "status": record.status,
    }
    if isinstance(record.value, Stage6Error):
        row["value"] = {
            "kind": "error",
            "status_code": record.value.status_code,
            "code": record.value.code,
            "message": record.value.message,
        }
    elif isinstance(record.value, MultilingualWalkthroughResult):
        row["value"] = {"kind": "result", "result": multilingual_result_to_dict(record.value)}
    else:
        row["value"] = {"kind": "none"}
    return row


def stage6_idempotency_record_from_dict(row: dict[str, Any]) -> Stage6IdempotencyRecord:
    value_ref = row.get("value", {})
    value: MultilingualWalkthroughResult | Stage6Error | None = None
    if isinstance(value_ref, dict):
        if value_ref.get("kind") == "error":
            value = Stage6Error(
                int(value_ref.get("status_code", 500)),
                str(value_ref.get("code", "INTERNAL_SERVER_ERROR")),
                str(value_ref.get("message", "Request failed.")),
            )
        elif value_ref.get("kind") == "result" and isinstance(value_ref.get("result"), dict):
            value = multilingual_result_from_dict(cast(dict[str, Any], value_ref["result"]))
    status = str(row["status"])
    if status not in {"PENDING", "RUNNING", "COMPLETED", "FAILED"}:
        raise ValueError(f"Unsupported Stage 6 idempotency status: {status}")
    if status == "COMPLETED" and value is None:
        raise ValueError("Completed Stage 6 idempotency record references missing value.")
    if status == "COMPLETED" and not isinstance(value, MultilingualWalkthroughResult):
        raise ValueError("Completed Stage 6 idempotency record references invalid value.")
    if status == "FAILED" and not isinstance(value, Stage6Error):
        raise ValueError("Failed Stage 6 idempotency record references missing error.")
    record = Stage6IdempotencyRecord(
        idempotency_scope=str(row["idempotency_scope"]),
        endpoint=str(row["endpoint"]),
        idempotency_key=str(row["idempotency_key"]),
        request_checksum=str(row["request_checksum"]),
        status=cast(Literal["PENDING", "RUNNING", "COMPLETED", "FAILED"], status),
        value=value,
    )
    if isinstance(record.value, MultilingualWalkthroughResult):
        validate_stage6_scope(
            idempotency_scope=record.idempotency_scope,
            tenant_id=record.value.tenant_id,
            project_id=record.value.project_id,
            actor_id=record.value.actor_id,
            source_run_id=record.value.source_run_id,
        )
    return record


def max_multilingual_run_suffix(records: dict[tuple[str, str, str], Stage6IdempotencyRecord]) -> int:
    maximum = 0
    for record in records.values():
        if not isinstance(record.value, MultilingualWalkthroughResult):
            continue
        identifier = record.value.multilingual_run_id
        if not identifier.startswith("mlrun_"):
            continue
        try:
            maximum = max(maximum, int(identifier.removeprefix("mlrun_")))
        except ValueError:
            continue
    return maximum


def max_multilingual_run_identifier(runs: dict[str, MultilingualWalkthroughResult]) -> int:
    maximum = 0
    for identifier in runs:
        if not identifier.startswith("mlrun_"):
            continue
        try:
            maximum = max(maximum, int(identifier.removeprefix("mlrun_")))
        except ValueError:
            continue
    return maximum


def multilingual_result_to_dict(result: MultilingualWalkthroughResult) -> dict[str, Any]:
    return asdict(result)


def multilingual_result_from_dict(row: dict[str, Any]) -> MultilingualWalkthroughResult:
    artifacts = cast(dict[str, Any], row["artifacts"])
    voice = cast(dict[str, Any], row["voice"])
    translation_provider = cast(dict[str, Any], row["translation_provider"])
    request_checksum = str(row["request_checksum"])
    tenant_id = validate_checksum_component(str(row["tenant_id"]), field_name="tenant identifier")
    project_id = validate_checksum_component(str(row["project_id"]), field_name="project identifier")
    actor_id = validate_checksum_component(str(row["actor_id"]), field_name="actor identifier")
    source_language = normalize_language_tag(str(row["source_language"]))
    target_language = normalize_language_tag(str(row["target_language"]))
    status = str(row["status"])
    if status != "COMPLETED":
        raise Stage6Error(422, "PROVIDER_OUTPUT_INVALID", "Restored Stage 6 result status is invalid.")
    translation_provider_id = validate_provider_id(
        str(translation_provider["provider"]),
        field_name="translation provider",
    )
    translation_provider_mode = validate_local_provider_mode(
        str(translation_provider["provider_mode"]),
        field_name="translation provider mode",
    )
    voice_provider_id = validate_provider_id(str(voice["provider"]), field_name="voice provider")
    voice_provider_mode = validate_provider_mode(str(voice["provider_mode"]))
    requested_voice_provider = validate_provider_id(str(voice["requested_provider"]), field_name="requested voice provider")
    fallback_reason = validate_voice_fallback_reason(
        str(voice["fallback_reason"]) if voice.get("fallback_reason") is not None else None
    )
    raw_voice_artifact = downloadable_artifact_from_dict(
        cast(dict[str, Any], voice["artifact"]),
        expected_mime_type="application/json",
        expected_extension=".json",
    )
    voice_artifact = validate_tts_manifest_artifact(raw_voice_artifact) if is_tts_manifest_artifact(
        raw_voice_artifact
    ) else validate_voice_manifest_artifact(raw_voice_artifact)
    voice_audio_artifact = None
    if voice.get("audio_artifact") is not None:
        voice_audio_artifact = downloadable_audio_artifact_from_dict(cast(dict[str, Any], voice["audio_artifact"]))
    elif artifacts.get("voice_audio") is not None:
        voice_audio_artifact = downloadable_audio_artifact_from_dict(cast(dict[str, Any], artifacts["voice_audio"]))
    translated_script_artifact = downloadable_artifact_from_dict(
        cast(dict[str, Any], artifacts["translated_script"]),
        expected_mime_type="text/markdown",
        expected_extension=".md",
    )
    subtitles_artifact = downloadable_artifact_from_dict(
        cast(dict[str, Any], artifacts["subtitles"]),
        expected_mime_type="application/x-subrip",
        expected_extension=".srt",
    )
    metadata_artifact = downloadable_artifact_from_dict(
        cast(dict[str, Any], artifacts["metadata"]),
        expected_mime_type="application/json",
        expected_extension=".json",
    )
    source_script_text = str(row["source_script_text"])
    source_text_checksum = validate_checksum_component(str(row["source_text_checksum"]), field_name="source text checksum")
    if source_text_checksum != checksum_text(source_script_text):
        raise Stage6Error(422, "PROVIDER_OUTPUT_INVALID", "Restored Stage 6 source text checksum is inconsistent.")
    translated_script_text = str(row["translated_script_text"])
    subtitles_text = str(row["subtitles_text"])
    provider_translated_text = str(translation_provider["translated_text"])
    if translated_script_text != provider_translated_text:
        raise Stage6Error(422, "PROVIDER_OUTPUT_INVALID", "Restored Stage 6 translated text is inconsistent.")
    if artifact_text(subtitles_artifact) != subtitles_text:
        raise Stage6Error(422, "PROVIDER_OUTPUT_INVALID", "Restored Stage 6 subtitle artifact is inconsistent.")
    if subtitles_text != generate_subtitles(script_text=translated_script_text, language=target_language):
        raise Stage6Error(422, "PROVIDER_OUTPUT_INVALID", "Restored Stage 6 subtitles are inconsistent.")
    validated_text, expected_preserved_terms, citation_count = validate_translation_output(
        source_text=source_script_text,
        translated_text=translated_script_text,
        glossary_terms=[str(term) for term in row.get("glossary_terms", [])],
    )
    if validated_text != translated_script_text:
        raise Stage6Error(422, "PROVIDER_OUTPUT_INVALID", "Restored Stage 6 translated text is inconsistent.")
    preserved_terms = [str(term) for term in row.get("preserved_terms", [])]
    provider_preserved_terms = [str(term) for term in translation_provider.get("preserved_terms", [])]
    if preserved_terms != expected_preserved_terms or provider_preserved_terms != expected_preserved_terms:
        raise Stage6Error(422, "PROVIDER_OUTPUT_INVALID", "Restored Stage 6 preserved glossary terms are inconsistent.")
    source_context_ref_count = int(row["source_context_ref_count"])
    source_citation_count = int(row["source_citation_count"])
    source_context_ref_ids = normalize_evidence_ids(
        tuple(str(value) for value in row.get("source_context_ref_ids", ())),
        count=source_context_ref_count,
        prefix="ctx_",
        field_name="source context reference identifiers",
    )
    source_citation_indexes = normalize_citation_indexes(
        tuple(int(value) for value in row.get("source_citation_indexes", ())),
        count=source_citation_count,
    )
    source_claim_support_ids = normalize_evidence_ids(
        tuple(str(value) for value in row.get("source_claim_support_ids", ())),
        count=source_citation_count,
        prefix="claimsup_",
        field_name="source claim-support identifiers",
    )
    if citation_count != source_citation_count:
        raise Stage6Error(422, "PROVIDER_OUTPUT_INVALID", "Restored Stage 6 citation count is inconsistent.")
    source_evaluation_id = normalize_evaluation_id(str(row["source_evaluation_id"]))
    evaluation_status = validate_evaluation_status(str(row["evaluation_status"]))
    source_evaluation_checksum = validate_source_evaluation_checksum(
        source_evaluation_checksum=str(row["source_evaluation_checksum"]),
        source_evaluation_id=source_evaluation_id,
        source_run_id=str(row["source_run_id"]),
        trace_id=str(row["trace_id"]),
        evaluation_status=evaluation_status,
        source_context_ref_ids=source_context_ref_ids,
        source_context_ref_count=source_context_ref_count,
        source_citation_indexes=source_citation_indexes,
        source_citation_count=source_citation_count,
    )
    transcript_segments = tuple(
        transcript_segment_from_any(cast(dict[str, Any], segment))
        for segment in row.get("transcript_segments", row.get("transcriptSegments", ()))
    )
    transcript_correctness = validate_multilingual_transcript_correctness(
        target_language=target_language,
        source_text=source_script_text,
        segments=transcript_segments,
        source_run_id=str(row["source_run_id"]),
        evaluation_id=source_evaluation_id,
        context_ref_ids=source_context_ref_ids,
        citation_indexes=source_citation_indexes,
        claim_support_ids=source_claim_support_ids,
    )
    validate_translated_script_matches_transcript(
        target_language=target_language,
        source_text=source_script_text,
        translated_script_text=translated_script_text,
        transcript_segments=transcript_segments,
    )
    expected_translated_script_artifact_text = render_translated_script_artifact_text(
        target_language=target_language,
        transcript_segments=transcript_segments,
        transcript_correctness=transcript_correctness,
    )
    if artifact_text(translated_script_artifact) != expected_translated_script_artifact_text:
        raise Stage6Error(422, "PROVIDER_OUTPUT_INVALID", "Restored Stage 6 script artifact is inconsistent.")
    expected_request_checksum = build_multilingual_request_checksum(
        source_script=source_script_text,
        source_language=source_language,
        target_language=target_language,
        requested_voice_provider=requested_voice_provider,
        glossary_terms=[str(term) for term in row.get("glossary_terms", [])],
        tenant_id=tenant_id,
        project_id=project_id,
        actor_id=actor_id,
        source_run_id=str(row["source_run_id"]),
        trace_id=str(row["trace_id"]),
        source_context_ref_count=source_context_ref_count,
        source_citation_count=source_citation_count,
        source_context_ref_ids=source_context_ref_ids,
        source_citation_indexes=source_citation_indexes,
        source_claim_support_ids=source_claim_support_ids,
        source_evaluation_id=source_evaluation_id,
        source_evaluation_checksum=source_evaluation_checksum,
        evaluation_status=evaluation_status,
    )
    if request_checksum != expected_request_checksum:
        raise Stage6Error(422, "PROVIDER_OUTPUT_INVALID", "Restored Stage 6 request checksum is inconsistent.")
    voice_manifest = json.loads(artifact_text(voice_artifact))
    if not restored_voice_manifest_matches(
        voice_manifest=voice_manifest,
        translation_provider=translation_provider,
        source_language=source_language,
        target_language=target_language,
        voice=voice,
        voice_provider_id=voice_provider_id,
        voice_provider_mode=voice_provider_mode,
        translated_script_text=translated_script_text,
        source_run_id=str(row["source_run_id"]),
        trace_id=str(row["trace_id"]),
        actor_id=actor_id,
        source_evaluation_id=source_evaluation_id,
        source_evaluation_checksum=source_evaluation_checksum,
        evaluation_status=evaluation_status,
        source_context_ref_count=source_context_ref_count,
        source_context_ref_ids=source_context_ref_ids,
        source_citation_count=source_citation_count,
        source_citation_indexes=source_citation_indexes,
        source_claim_support_ids=source_claim_support_ids,
        audio_artifact=voice_audio_artifact,
    ):
        raise Stage6Error(422, "PROVIDER_OUTPUT_INVALID", "Restored Stage 6 voice manifest is inconsistent.")
    expected_metadata_text = build_stage6_metadata_text(
        multilingual_run_id=str(row["multilingual_run_id"]),
        request_checksum=request_checksum,
        tenant_id=tenant_id,
        project_id=project_id,
        actor_id=actor_id,
        source_run_id=str(row["source_run_id"]),
        trace_id=str(row["trace_id"]),
        source_language=source_language,
        target_language=target_language,
        source_text_checksum=source_text_checksum,
        source_context_ref_count=source_context_ref_count,
        source_context_ref_ids=source_context_ref_ids,
        source_citation_count=source_citation_count,
        source_citation_indexes=source_citation_indexes,
        source_claim_support_ids=source_claim_support_ids,
        source_evaluation_id=source_evaluation_id,
        source_evaluation_checksum=source_evaluation_checksum,
        evaluation_status=evaluation_status,
        glossary_terms=[str(term) for term in row.get("glossary_terms", [])],
        preserved_terms=expected_preserved_terms,
        source_script_text=source_script_text,
        translated_script_text=translated_script_text,
        transcript_segments=transcript_segments,
        transcript_correctness=transcript_correctness,
        translation_provider=TranslationProviderResult(
            provider=translation_provider_id,
            provider_mode=translation_provider_mode,
            source_language=normalize_language_tag(str(translation_provider["source_language"])),
            target_language=normalize_language_tag(str(translation_provider["target_language"])),
            translated_text=provider_translated_text,
            preserved_terms=provider_preserved_terms,
        ),
        voice=VoiceProviderResult(
            provider=voice_provider_id,
            provider_mode=voice_provider_mode,
            requested_provider=requested_voice_provider,
            fallback_reason=fallback_reason,
            language=normalize_language_tag(str(voice["language"])),
            artifact=voice_artifact,
            audio_artifact=voice_audio_artifact,
        ),
        translated_script_artifact=translated_script_artifact,
        subtitles_artifact=subtitles_artifact,
    )
    if artifact_text(metadata_artifact) != expected_metadata_text:
        raise Stage6Error(422, "PROVIDER_OUTPUT_INVALID", "Restored Stage 6 metadata artifact is inconsistent.")
    return MultilingualWalkthroughResult(
        multilingual_run_id=str(row["multilingual_run_id"]),
        request_checksum=request_checksum,
        tenant_id=tenant_id,
        project_id=project_id,
        actor_id=actor_id,
        source_run_id=str(row["source_run_id"]),
        source_language=source_language,
        target_language=target_language,
        status=status,
        source_script_text=source_script_text,
        source_text_checksum=source_text_checksum,
        translated_script_text=translated_script_text,
        subtitles_text=subtitles_text,
        transcript_segments=transcript_segments,
        transcript_correctness=transcript_correctness,
        glossary_terms=[str(term) for term in row.get("glossary_terms", [])],
        preserved_terms=expected_preserved_terms,
        translation_provider=TranslationProviderResult(
            provider=translation_provider_id,
            provider_mode=translation_provider_mode,
            source_language=normalize_language_tag(str(translation_provider["source_language"])),
            target_language=normalize_language_tag(str(translation_provider["target_language"])),
            translated_text=provider_translated_text,
            preserved_terms=provider_preserved_terms,
        ),
        voice=VoiceProviderResult(
            provider=voice_provider_id,
            provider_mode=voice_provider_mode,
            requested_provider=requested_voice_provider,
            fallback_reason=fallback_reason,
            language=normalize_language_tag(str(voice["language"])),
            artifact=voice_artifact,
            audio_artifact=voice_audio_artifact,
        ),
        artifacts=MultilingualArtifacts(
            translated_script=translated_script_artifact,
            subtitles=subtitles_artifact,
            voice_manifest=voice_artifact,
            metadata=metadata_artifact,
            voice_audio=voice_audio_artifact,
        ),
        trace_id=str(row["trace_id"]),
        source_context_ref_count=source_context_ref_count,
        source_citation_count=source_citation_count,
        source_context_ref_ids=source_context_ref_ids,
        source_citation_indexes=source_citation_indexes,
        source_claim_support_ids=source_claim_support_ids,
        source_evaluation_id=source_evaluation_id,
        source_evaluation_checksum=source_evaluation_checksum,
        evaluation_status=evaluation_status,
    )


def artifact_text(artifact: DownloadableArtifact) -> str:
    try:
        return _decode_artifact_content(artifact.content_base64, field_name="Downloadable artifact")
    except Stage6Error:
        raise
    except (binascii.Error, TypeError, UnicodeDecodeError) as exc:
        raise Stage6Error(422, "PROVIDER_OUTPUT_INVALID", "Downloadable artifact content is invalid.") from exc


def _decode_artifact_content(content_base64: str, *, field_name: str) -> str:
    if len(content_base64) > MAX_STAGE6_ARTIFACT_BASE64_CHARS:
        raise Stage6Error(413, "PROVIDER_OUTPUT_TOO_LARGE", f"{field_name} exceeds the Stage 6 limit.")
    try:
        decoded_bytes = base64.b64decode(content_base64, validate=True)
    except (binascii.Error, TypeError) as exc:
        raise Stage6Error(422, "PROVIDER_OUTPUT_INVALID", f"{field_name} content is invalid.") from exc
    if len(decoded_bytes) > MAX_STAGE6_ARTIFACT_BYTES:
        raise Stage6Error(413, "PROVIDER_OUTPUT_TOO_LARGE", f"{field_name} exceeds the Stage 6 limit.")
    try:
        return decoded_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise Stage6Error(422, "PROVIDER_OUTPUT_INVALID", f"{field_name} content is invalid.") from exc


def downloadable_artifact_from_dict(
    row: dict[str, Any],
    *,
    expected_mime_type: str,
    expected_extension: str,
) -> DownloadableArtifact:
    artifact = DownloadableArtifact(
        file_name=str(row["file_name"]),
        mime_type=str(row["mime_type"]),
        content_base64=str(row["content_base64"]),
        checksum=str(row["checksum"]),
    )
    return validate_downloadable_artifact(
        artifact,
        expected_mime_type=expected_mime_type,
        expected_extension=expected_extension,
    )


def downloadable_audio_artifact_from_dict(row: dict[str, Any]) -> DownloadableArtifact:
    artifact = DownloadableArtifact(
        file_name=str(row["file_name"]),
        mime_type=str(row["mime_type"]),
        content_base64=str(row["content_base64"]),
        checksum=str(row["checksum"]),
    )
    return validate_audio_artifact(artifact)


def create_stage6_service(*, state_path: Path | None = None) -> Stage6Service:
    return Stage6Service(state_path=state_path)


def get_language_catalog() -> tuple[LanguageCatalogRecord, ...]:
    return LANGUAGE_CATALOG


def language_catalog_record_to_api(record: LanguageCatalogRecord) -> dict[str, object]:
    return {
        "languageTag": record.language_tag,
        "englishName": record.english_name,
        "nativeName": record.native_name,
        "label": f"{record.english_name} / {record.native_name}",
        "script": record.script,
        "direction": record.direction,
        "marketPriority": record.market_priority,
        "regionGroup": record.region_group,
        "localDemoSupportStatus": record.local_demo_support_status,
        "providerSupportStatus": record.provider_support_status,
        "testCoverageLevel": record.test_coverage_level,
    }


def transcript_segment_to_api(segment: MultilingualTranscriptSegment) -> dict[str, object]:
    return {
        "segmentId": segment.segment_id,
        "sourceText": segment.source_text,
        "targetLanguage": segment.target_language,
        "targetText": segment.target_text,
        "englishReferenceText": segment.english_reference_text,
        "citationMarkers": list(segment.citation_markers),
        "citationIndexes": list(segment.citation_indexes),
        "contextRefIds": list(segment.context_ref_ids),
        "claimSupportIds": list(segment.claim_support_ids),
        "sourceRunId": segment.source_run_id,
        "evaluationId": segment.evaluation_id,
    }


def transcript_correctness_to_api(correctness: TranscriptCorrectness) -> dict[str, object]:
    return {
        "validationStatus": correctness.validation_status,
        "script": correctness.script,
        "direction": correctness.direction,
        "segmentCount": correctness.segment_count,
        "citationIndexes": list(correctness.citation_indexes),
    }


def build_multilingual_request_checksum(
    *,
    source_script: str,
    source_language: str,
    target_language: str,
    requested_voice_provider: str,
    glossary_terms: list[str],
    tenant_id: str = "tenant",
    project_id: str = "project",
    actor_id: str = "user",
    source_run_id: str,
    trace_id: str,
    source_context_ref_count: int,
    source_citation_count: int,
    source_context_ref_ids: tuple[str, ...] | None,
    source_citation_indexes: tuple[int, ...] | None,
    source_claim_support_ids: tuple[str, ...] | None,
    source_evaluation_id: str,
    source_evaluation_checksum: str,
    evaluation_status: str,
) -> str:
    normalized_source_script = source_script.strip()
    normalized_source_language = normalize_language_tag(source_language)
    normalized_target_language = normalize_language_tag(target_language)
    normalized_requested_voice_provider = validate_provider_id(
        requested_voice_provider or "mock",
        field_name="requested voice provider",
    )
    normalized_glossary_terms = normalize_glossary_terms(glossary_terms)
    normalized_source_evaluation_id = normalize_evaluation_id(source_evaluation_id)
    normalized_evaluation_status = validate_evaluation_status(evaluation_status)
    return checksum_text(
        json.dumps(
            {
                "evaluationStatus": normalized_evaluation_status,
                "actorId": actor_id,
                "glossaryTerms": normalized_glossary_terms,
                "requestedVoiceProvider": normalized_requested_voice_provider,
                "projectId": project_id,
                "sourceCitationCount": source_citation_count,
                "sourceCitationIndexes": list(source_citation_indexes) if source_citation_indexes is not None else None,
                "sourceClaimSupportIds": list(source_claim_support_ids) if source_claim_support_ids is not None else None,
                "sourceContextRefCount": source_context_ref_count,
                "sourceContextRefIds": list(source_context_ref_ids) if source_context_ref_ids is not None else None,
                "sourceEvaluationChecksum": source_evaluation_checksum,
                "sourceEvaluationId": normalized_source_evaluation_id,
                "sourceLanguage": normalized_source_language,
                "sourceRunId": source_run_id,
                "sourceScript": normalized_source_script,
                "sourceTextChecksum": checksum_text(normalized_source_script),
                "tenantId": tenant_id,
                "targetLanguage": normalized_target_language,
                "traceId": trace_id,
            },
            sort_keys=True,
            separators=(",", ":"),
        )
    )


def normalize_language_tag(language: str) -> str:
    raw_language = language.strip()
    if not raw_language:
        raise Stage6Error(422, "UNSUPPORTED_LANGUAGE", "Unsupported target language.")
    canonical_by_lower = {tag.lower(): tag for tag in LANGUAGE_CATALOG_BY_TAG}
    lowered = raw_language.lower()
    if lowered in canonical_by_lower:
        canonical = canonical_by_lower[lowered]
        record = LANGUAGE_CATALOG_BY_TAG[canonical]
        if record.local_demo_support_status != "SUPPORTED":
            raise Stage6Error(
                422,
                "LOCAL_DEMO_LANGUAGE_UNSUPPORTED",
                f"{record.english_name} is cataloged as planned and unsupported in the local demo.",
            )
        return canonical
    try:
        normalized = langcodes.standardize_tag(raw_language)
        base_language = langcodes.Language.get(normalized).language
    except (LookupError, ValueError) as exc:
        raise Stage6Error(422, "UNSUPPORTED_LANGUAGE", "Unsupported target language.") from exc
    if base_language not in SUPPORTED_LANGUAGES:
        raise Stage6Error(422, "UNSUPPORTED_LANGUAGE", "Unsupported target language.")
    return base_language


def source_transcript_segments(source_text: str) -> tuple[tuple[str, tuple[str, ...], tuple[int, ...]], ...]:
    matches = list(re.finditer(r"(?P<text>.*?\[(?P<index>\d+)\])(?:\s+|$)", source_text, flags=re.DOTALL))
    if not matches:
        return ((source_text.strip(), (), ()),)
    segments: list[tuple[str, tuple[str, ...], tuple[int, ...]]] = []
    previous_end = 0
    for match in matches:
        uncovered = source_text[previous_end : match.start()].strip()
        if uncovered:
            raise Stage6Error(
                422,
                "TRANSCRIPT_CORRECTNESS_FAILED",
                "Source English text contains uncited content outside transcript segments.",
            )
        text = " ".join(match.group("text").strip().split())
        index = int(match.group("index"))
        if re.fullmatch(r"(?:\[\d+\]\s*)+", text) and segments:
            previous_text, previous_markers, previous_indexes = segments[-1]
            segments[-1] = (
                f"{previous_text} {text}",
                previous_markers + (f"[{index}]",),
                previous_indexes + (index,),
            )
            previous_end = match.end()
            continue
        segments.append((text, (f"[{index}]",), (index,)))
        previous_end = match.end()
    trailing = source_text[previous_end:].strip()
    if trailing:
        raise Stage6Error(
            422,
            "TRANSCRIPT_CORRECTNESS_FAILED",
            "Source English text contains uncited content outside transcript segments.",
        )
    return tuple(segments)


def translate_demo_source_text(*, source_text: str, target_language: str) -> str:
    return " ".join(
        translate_demo_segment_text(
            segment_number=index,
            source_segment=segment_text,
            target_language=target_language,
            citation_markers=markers,
        )
        for index, (segment_text, markers, _citation_indexes) in enumerate(source_transcript_segments(source_text), start=1)
    )


def translate_demo_segment_text(
    *,
    segment_number: int,
    source_segment: str,
    target_language: str,
    citation_markers: tuple[str, ...],
) -> str:
    if target_language == "en":
        target = source_segment
    else:
        base_text = local_demo_translated_segment_fixture(
            source_segment=source_segment,
            target_language=target_language,
        )
        if base_text is None:
            raise Stage6Error(
                422,
                "LOCAL_DEMO_TRANSLATION_UNSUPPORTED",
                "Local demo translation is only available for controlled acceptance fixture scripts.",
            )
        target = base_text
    suffix = " ".join(citation_markers)
    if suffix and not target.endswith(suffix):
        target = f"{target} {suffix}"
    if len(source_transcript_segments(source_segment)) == 1 and citation_markers:
        return target
    return target


def local_demo_translated_segment_fixture(*, source_segment: str, target_language: str) -> str | None:
    normalized_source = normalize_local_demo_fixture_source_segment(source_segment)
    source_body = local_demo_fixture_source_body(normalized_source)
    if local_demo_source_has_unknown_audience_prefix(
        source_segment=normalized_source,
        target_language=target_language,
    ):
        return None
    atlas_fixture_translation = ATLAS_OUTPUT_FIXTURE_TRANSLATIONS.get(source_body)
    if atlas_fixture_translation is not None:
        return local_demo_with_audience_prefix(
            source_segment=source_segment,
            target_language=target_language,
            base_text=atlas_fixture_translation.get(target_language),
        )
    if (
        source_body
        == "Helio Media MEDIA-SENTINEL-CP4 is a fictional local onboarding studio for field operations teams."
    ):
        return local_demo_with_audience_prefix(
            source_segment=source_segment,
            target_language=target_language,
            base_text=HELIO_MEDIA_TRANSLATED_SEGMENT_TEXT.get(target_language),
        )
    if source_body in {
        "NarraTwin AI turns approved project knowledge into grounded walkthrough scripts.",
        "NarraTwin AI turns approved project knowledge into grounded walkthrough scripts with source chunk citations.",
        "NarraTwin AI creates grounded walkthrough scripts.",
    }:
        base_text = DEMO_TRANSLATED_SEGMENT_TEXT.get(target_language)
        if base_text is None:
            return None
        audience_prefix = local_demo_translated_audience_prefix(
            source_segment=source_segment,
            target_language=target_language,
        )
        return f"{audience_prefix}, {base_text}" if audience_prefix else base_text
    if (
        target_language == "es"
        and source_body
        in {
            "NarraTwin AI creates grounded walkthrough scripts. FAST_SUCCESS",
            "NarraTwin AI creates grounded walkthrough scripts. SLOW_FAILURE",
        }
    ):
        marker = source_body.rsplit(" ", maxsplit=1)[-1]
        base_text = DEMO_TRANSLATED_SEGMENT_TEXT.get(target_language)
        if base_text is None:
            return None
        return f"{base_text} {marker}"
    if (
        source_body
        == "It supports recruiters, hiring managers, engineers, product leaders, customers, beginners, and global audiences with audience-aware explanations."
    ):
        return local_demo_with_audience_prefix(
            source_segment=source_segment,
            target_language=target_language,
            base_text=DEMO_AUDIENCE_SUPPORT_TEXT.get(target_language),
        )
    if source_body == "It supports recruiter and engineering audiences with audience-aware explanations.":
        return local_demo_with_audience_prefix(
            source_segment=source_segment,
            target_language=target_language,
            base_text=DEMO_RECRUITER_ENGINEERING_SUPPORT_TEXT.get(target_language),
        )
    if source_body == "The local demo uses mock local LLM, translation, voice, and avatar adapters for deterministic review.":
        return local_demo_with_audience_prefix(
            source_segment=source_segment,
            target_language=target_language,
            base_text=DEMO_LOCAL_PROVIDER_TEXT.get(target_language),
        )
    if source_body == "The Stage 4 slice uses a mock local LLM and mock local embeddings for deterministic tests.":
        return local_demo_with_audience_prefix(
            source_segment=source_segment,
            target_language=target_language,
            base_text=DEMO_STAGE4_SLICE_TEXT.get(target_language),
        )
    if source_body == "Every generated walkthrough claim must cite retrieved source chunks from approved knowledge.":
        return local_demo_with_audience_prefix(
            source_segment=source_segment,
            target_language=target_language,
            base_text=DEMO_CITATION_REQUIREMENT_TEXT.get(target_language),
        )
    return None


def normalize_local_demo_fixture_source_segment(source_segment: str) -> str:
    normalized = " ".join(source_segment.strip().split())
    return re.sub(r"(?:\s*\[\d+\])+$", "", normalized).strip()


def local_demo_fixture_source_body(source_segment: str) -> str:
    return re.sub(r"^For [^,]+,\s+", "", source_segment).strip()


def local_demo_source_has_unknown_audience_prefix(*, source_segment: str, target_language: str) -> bool:
    match = re.match(r"\s*For (?P<audience>[^,]+),\s+", source_segment)
    if not match:
        return False
    audience = " ".join(match.group("audience").lower().split())
    return audience not in DEMO_AUDIENCE_PREFIX_TEXT.get(target_language, {})


def local_demo_with_audience_prefix(*, source_segment: str, target_language: str, base_text: str | None) -> str | None:
    if base_text is None:
        return None
    audience_prefix = local_demo_translated_audience_prefix(
        source_segment=source_segment,
        target_language=target_language,
    )
    return f"{audience_prefix}, {base_text}" if audience_prefix else base_text


def local_demo_translated_audience_prefix(*, source_segment: str, target_language: str) -> str | None:
    match = re.match(r"\s*For (?P<audience>[^,]+),\s+", source_segment)
    if not match:
        return None
    audience = " ".join(match.group("audience").lower().split())
    return DEMO_AUDIENCE_PREFIX_TEXT.get(target_language, {}).get(audience)


def translated_script_text_from_transcript_segments(
    segments: Iterable[MultilingualTranscriptSegment],
) -> str:
    return " ".join(segment.target_text for segment in segments)


def render_translated_script_artifact_text(
    *,
    target_language: str,
    transcript_segments: tuple[MultilingualTranscriptSegment, ...],
    transcript_correctness: TranscriptCorrectness,
) -> str:
    lines = [
        "# Multilingual transcript",
        "",
        f"Target language: {target_language}",
        f"Script: {transcript_correctness.script}",
        f"Direction: {transcript_correctness.direction}",
        "",
    ]
    for segment in transcript_segments:
        lines.extend(
            [
                f"## {segment.segment_id}",
                "",
                f"Source English: {segment.source_text}",
                "",
                f"Target ({segment.target_language}): {segment.target_text}",
                "",
                f"English reference: {segment.english_reference_text}",
                "",
                f"Citations: {', '.join(segment.citation_markers)}",
                "",
                f"Context refs: {', '.join(segment.context_ref_ids)}",
                f"Claim support ids: {', '.join(segment.claim_support_ids)}",
                f"Source run id: {segment.source_run_id}",
                f"Evaluation id: {segment.evaluation_id}",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def validate_translated_script_matches_transcript(
    *,
    target_language: str,
    source_text: str,
    translated_script_text: str,
    transcript_segments: tuple[MultilingualTranscriptSegment, ...],
) -> None:
    if target_language == "en":
        return
    expected_text = translated_script_text_from_transcript_segments(transcript_segments)
    if translated_script_text != expected_text:
        raise Stage6Error(
            422,
            "PROVIDER_OUTPUT_INVALID",
            "Translated script does not match validated transcript segments.",
        )


def build_multilingual_transcript_segments(
    *,
    source_text: str,
    target_language: str,
    source_run_id: str,
    source_evaluation_id: str,
    source_context_ref_ids: tuple[str, ...],
    source_claim_support_ids: tuple[str, ...],
) -> tuple[MultilingualTranscriptSegment, ...]:
    source_segments = source_transcript_segments(source_text)
    context_by_citation = dict(zip(citation_marker_sequence(source_text), source_context_ref_ids, strict=False))
    claim_by_citation = dict(zip(citation_marker_sequence(source_text), source_claim_support_ids, strict=False))
    segments: list[MultilingualTranscriptSegment] = []
    for index, (source_segment, markers, citation_indexes) in enumerate(source_segments, start=1):
        context_ref_ids = tuple(context_by_citation.get(marker.strip("[]"), "") for marker in markers)
        claim_support_ids = tuple(claim_by_citation.get(marker.strip("[]"), "") for marker in markers)
        segments.append(
            MultilingualTranscriptSegment(
                segment_id=f"seg_{index:03d}",
                source_text=source_segment,
                target_language=target_language,
                target_text=translate_demo_segment_text(
                    segment_number=index,
                    source_segment=source_segment,
                    target_language=target_language,
                    citation_markers=markers,
                ),
                english_reference_text=source_segment,
                citation_markers=markers,
                citation_indexes=citation_indexes,
                context_ref_ids=tuple(value for value in context_ref_ids if value),
                claim_support_ids=tuple(value for value in claim_support_ids if value),
                source_run_id=source_run_id,
                evaluation_id=source_evaluation_id,
            )
        )
    return tuple(segments)


SCRIPT_PATTERNS = {
    "Devanagari": re.compile(r"[\u0900-\u097F]"),
    "Arabic": re.compile(r"[\u0600-\u06FF]"),
    "Hebrew": re.compile(r"[\u0590-\u05FF]"),
    "Cyrillic": re.compile(r"[\u0400-\u04FF]"),
    "Japanese": re.compile(r"[\u3040-\u30FF\u4E00-\u9FFF]"),
    "Hangul": re.compile(r"[\uAC00-\uD7AF]"),
    "Thai": re.compile(r"[\u0E00-\u0E7F]"),
}
UNTRANSLATED_DOMAIN_TERM_PATTERNS = (
    re.compile(r"\bwalkthrough\b", re.IGNORECASE),
)
TRANSLITERATED_SOURCE_DOMAIN_TERM_PATTERNS_BY_LANGUAGE = {
    "hi": (
        re.compile(r"जनरेट"),
        re.compile(r"वॉकथ्रू"),
        re.compile(r"मॉक"),
        re.compile(r"डेमो"),
        re.compile(r"अडैप्टर"),
        re.compile(r"एम्बेडिंग"),
        re.compile(r"स्लाइस"),
    ),
    "ja": (
        re.compile(r"ウォークスルー"),
        re.compile(r"チャンク"),
        re.compile(r"ローカルデモ"),
        re.compile(r"アダプター"),
        re.compile(r"アバター"),
        re.compile(r"スライス"),
    ),
    "ko": (
        re.compile(r"데모"),
        re.compile(r"어댑터"),
        re.compile(r"아바타"),
        re.compile(r"임베딩"),
        re.compile(r"슬라이스"),
    ),
    "ar": (re.compile(r"الأفاتار"),),
    "arz": (re.compile(r"الأفاتار"),),
    "he": (
        re.compile(r"הדמו"),
        re.compile(r"אווטאר"),
    ),
}


def validate_target_script(*, record: LanguageCatalogRecord, target_text: str, source_text: str) -> None:
    if record.language_tag == "en":
        return
    if target_text.strip() == source_text.strip():
        raise Stage6Error(422, "TRANSCRIPT_CORRECTNESS_FAILED", "Target transcript is an English fallback.")
    if record.language_tag == "zh-Hans" and not any(character in target_text for character in ("简", "项", "师", "转", "发", "检")):
        raise Stage6Error(422, "TRANSCRIPT_CORRECTNESS_FAILED", "Simplified Chinese transcript script is invalid.")
    if record.language_tag == "zh-Hant" and not any(character in target_text for character in ("繁", "專", "師", "轉", "發", "檢")):
        raise Stage6Error(422, "TRANSCRIPT_CORRECTNESS_FAILED", "Traditional Chinese transcript script is invalid.")
    pattern = SCRIPT_PATTERNS.get(record.script)
    if pattern is not None and not pattern.search(target_text):
        raise Stage6Error(422, "TRANSCRIPT_CORRECTNESS_FAILED", f"{record.script} transcript script is invalid.")
    if any(pattern.search(target_text) for pattern in UNTRANSLATED_DOMAIN_TERM_PATTERNS):
        raise Stage6Error(
            422,
            "TRANSCRIPT_CORRECTNESS_FAILED",
            "Target transcript contains untranslated source-domain terms.",
        )
    if any(
        pattern.search(target_text)
        for pattern in TRANSLITERATED_SOURCE_DOMAIN_TERM_PATTERNS_BY_LANGUAGE.get(record.language_tag, ())
    ):
        raise Stage6Error(
            422,
            "TRANSCRIPT_CORRECTNESS_FAILED",
            "Target transcript contains transliterated source-domain terms.",
        )


def validate_multilingual_transcript_correctness(
    *,
    target_language: str | None = None,
    language_tag: str | None = None,
    source_text: str,
    segments: Iterable[MultilingualTranscriptSegment | dict[str, Any]],
    source_run_id: str,
    evaluation_id: str,
    context_ref_ids: tuple[str, ...],
    citation_indexes: tuple[int, ...],
    claim_support_ids: tuple[str, ...],
) -> TranscriptCorrectness:
    target_language = target_language or language_tag
    if target_language is None:
        raise Stage6Error(422, "UNSUPPORTED_LANGUAGE", "Unsupported target language.")
    record = LANGUAGE_CATALOG_BY_TAG[target_language]
    normalized_segments = tuple(transcript_segment_from_any(segment) for segment in segments)
    if not normalized_segments:
        raise Stage6Error(422, "TRANSCRIPT_CORRECTNESS_FAILED", "Transcript segments are required.")
    source_segments = source_transcript_segments(source_text)
    if len(normalized_segments) != len(source_segments):
        raise Stage6Error(422, "TRANSCRIPT_CORRECTNESS_FAILED", "Transcript does not cover every cited source segment.")
    expected_indexes: list[int] = []
    for index, (segment, expected_source) in enumerate(zip(normalized_segments, source_segments, strict=True), start=1):
        source_segment, markers, indexes = expected_source
        expected_context_refs = tuple(
            context_ref_ids[citation_indexes.index(citation_index)]
            for citation_index in indexes
            if citation_index in citation_indexes
        )
        expected_claim_supports = tuple(
            claim_support_ids[citation_indexes.index(citation_index)]
            for citation_index in indexes
            if citation_index in citation_indexes
        )
        if segment.segment_id != f"seg_{index:03d}":
            raise Stage6Error(422, "TRANSCRIPT_CORRECTNESS_FAILED", "Transcript segment order is invalid.")
        if segment.source_text != source_segment:
            raise Stage6Error(422, "TRANSCRIPT_CORRECTNESS_FAILED", "Source English text is missing or drifted.")
        if segment.target_language != target_language:
            raise Stage6Error(422, "TRANSCRIPT_CORRECTNESS_FAILED", "Transcript target language binding is invalid.")
        if not segment.target_text.strip():
            raise Stage6Error(422, "TRANSCRIPT_CORRECTNESS_FAILED", "Target transcript text is missing.")
        if not segment.english_reference_text.strip():
            raise Stage6Error(422, "TRANSCRIPT_CORRECTNESS_FAILED", "English reference text is missing.")
        if segment.english_reference_text != source_segment:
            raise Stage6Error(422, "TRANSCRIPT_CORRECTNESS_FAILED", "English reference text does not match source.")
        if segment.citation_markers != markers or segment.citation_indexes != indexes:
            raise Stage6Error(422, "TRANSCRIPT_CORRECTNESS_FAILED", "Citation sequence drifted.")
        if any(marker not in segment.target_text for marker in markers):
            raise Stage6Error(422, "TRANSCRIPT_CORRECTNESS_FAILED", "Target transcript lost citation markers.")
        expected_target_text = translate_demo_segment_text(
            segment_number=index,
            source_segment=source_segment,
            target_language=target_language,
            citation_markers=markers,
        )
        if segment.target_text != expected_target_text:
            raise Stage6Error(
                422,
                "TRANSCRIPT_CORRECTNESS_FAILED",
                "Target transcript does not match the deterministic local-demo fixture.",
            )
        if segment.source_run_id != source_run_id or segment.evaluation_id != evaluation_id:
            raise Stage6Error(422, "TRANSCRIPT_CORRECTNESS_FAILED", "Source or evaluation binding is missing.")
        if segment.context_ref_ids != expected_context_refs or segment.claim_support_ids != expected_claim_supports:
            raise Stage6Error(422, "TRANSCRIPT_CORRECTNESS_FAILED", "Context or claim-support binding is missing.")
        validate_target_script(record=record, target_text=segment.target_text, source_text=source_segment)
        expected_indexes.extend(indexes)
    if tuple(expected_indexes) != citation_indexes:
        raise Stage6Error(422, "TRANSCRIPT_CORRECTNESS_FAILED", "Transcript citation coverage is incomplete.")
    return TranscriptCorrectness(
        validation_status="PASSED",
        script=record.script,
        direction=record.direction,
        segment_count=len(normalized_segments),
        citation_indexes=tuple(expected_indexes),
    )


def transcript_segment_from_any(value: MultilingualTranscriptSegment | dict[str, Any]) -> MultilingualTranscriptSegment:
    if isinstance(value, MultilingualTranscriptSegment):
        return value
    return MultilingualTranscriptSegment(
        segment_id=str(value["segmentId"] if "segmentId" in value else value["segment_id"]),
        source_text=str(value["sourceText"] if "sourceText" in value else value["source_text"]),
        target_language=str(value["targetLanguage"] if "targetLanguage" in value else value["target_language"]),
        target_text=str(value["targetText"] if "targetText" in value else value["target_text"]),
        english_reference_text=str(
            value["englishReferenceText"] if "englishReferenceText" in value else value["english_reference_text"]
        ),
        citation_markers=tuple(str(entry) for entry in value.get("citationMarkers", value.get("citation_markers", ()))),
        citation_indexes=tuple(int(entry) for entry in value.get("citationIndexes", value.get("citation_indexes", ()))),
        context_ref_ids=tuple(str(entry) for entry in value.get("contextRefIds", value.get("context_ref_ids", ()))),
        claim_support_ids=tuple(str(entry) for entry in value.get("claimSupportIds", value.get("claim_support_ids", ()))),
        source_run_id=str(value["sourceRunId"] if "sourceRunId" in value else value["source_run_id"]),
        evaluation_id=str(value["evaluationId"] if "evaluationId" in value else value["evaluation_id"]),
    )


def normalize_glossary_terms(terms: Iterable[str]) -> list[str]:
    normalized: list[str] = []
    for term in terms:
        candidate = " ".join(term.strip().split())
        if not candidate:
            raise Stage6Error(422, "VALIDATION_ERROR", "Glossary terms must not be blank.")
        if len(candidate) > MAX_GLOSSARY_TERM_CHARS:
            raise Stage6Error(422, "VALIDATION_ERROR", "Glossary term exceeds the Stage 6 limit.")
        if candidate not in normalized:
            normalized.append(candidate)
        if len(normalized) > MAX_GLOSSARY_TERMS:
            raise Stage6Error(422, "VALIDATION_ERROR", "Too many glossary terms for Stage 6.")
    return normalized


def validate_translation_output(
    *,
    source_text: str,
    translated_text: str,
    glossary_terms: list[str],
) -> tuple[str, list[str], int]:
    cleaned = translated_text.strip()
    if not cleaned:
        raise Stage6Error(422, "PROVIDER_OUTPUT_INVALID", "Translation provider returned empty output.")
    if len(cleaned) > MAX_SOURCE_SCRIPT_CHARS:
        raise Stage6Error(413, "PROVIDER_OUTPUT_TOO_LARGE", "Translation provider output exceeds the Stage 6 limit.")

    missing_terms = [term for term in glossary_terms if term in source_text and term not in cleaned]
    if missing_terms:
        raise Stage6Error(422, "PROVIDER_OUTPUT_INVALID", "Translation provider did not preserve required glossary terms.")

    source_markers = citation_marker_sequence(source_text)
    translated_markers = citation_marker_sequence(cleaned)
    if source_markers != translated_markers:
        raise Stage6Error(422, "PROVIDER_OUTPUT_INVALID", "Translation provider did not preserve citation markers.")

    return cleaned, [term for term in glossary_terms if term in cleaned], len(set(source_markers))


def citation_markers(text: str) -> set[str]:
    return set(re.findall(r"\[(\d+)\]", text))


def citation_marker_sequence(text: str) -> list[str]:
    return re.findall(r"\[(\d+)\]", text)


def validate_checksum_component(value: str, *, field_name: str) -> str:
    candidate = value.strip()
    if not candidate or CHECKSUM_COMPONENT_DELIMITER_PATTERN.search(candidate):
        raise Stage6Error(422, "PROVIDER_OUTPUT_INVALID", f"Invalid {field_name}.")
    return candidate


def normalize_evidence_ids(
    values: tuple[str, ...] | None,
    *,
    count: int,
    prefix: str,
    field_name: str,
) -> tuple[str, ...]:
    if count < 0:
        raise Stage6Error(422, "PROVIDER_OUTPUT_INVALID", f"Invalid {field_name}.")
    normalized = tuple(validate_checksum_component(value, field_name=field_name) for value in (values or ()))
    if count == 0:
        if normalized:
            raise Stage6Error(422, "PROVIDER_OUTPUT_INVALID", f"Invalid {field_name}.")
        return ()
    if len(normalized) != count or any(not value.startswith(prefix) for value in normalized):
        raise Stage6Error(422, "PROVIDER_OUTPUT_INVALID", f"Invalid {field_name}.")
    return normalized


def normalize_citation_indexes(values: tuple[int, ...] | None, *, count: int) -> tuple[int, ...]:
    normalized = tuple(int(value) for value in (values or ()))
    if count == 0:
        if normalized:
            raise Stage6Error(422, "PROVIDER_OUTPUT_INVALID", "Invalid source citation indexes.")
        return ()
    if len(normalized) != count or any(value <= 0 for value in normalized):
        raise Stage6Error(422, "PROVIDER_OUTPUT_INVALID", "Invalid source citation indexes.")
    return normalized


def normalize_evaluation_id(value: str) -> str:
    candidate = validate_checksum_component(value, field_name="source evaluation identifier")
    if not candidate.startswith("eval_"):
        raise Stage6Error(422, "PROVIDER_OUTPUT_INVALID", "Invalid source evaluation identifier.")
    return candidate


def validate_evaluation_status(value: str) -> EvaluationStatus:
    candidate = value.strip().upper()
    if candidate not in {"PASSED", "FAILED", "UNKNOWN"}:
        raise Stage6Error(422, "PROVIDER_OUTPUT_INVALID", "Invalid source evaluation status.")
    return cast(EvaluationStatus, candidate)


def validate_source_evaluation_checksum(
    *,
    source_evaluation_checksum: str,
    source_evaluation_id: str,
    source_run_id: str,
    trace_id: str,
    evaluation_status: EvaluationStatus,
    source_context_ref_ids: tuple[str, ...],
    source_context_ref_count: int,
    source_citation_indexes: tuple[int, ...],
    source_citation_count: int,
) -> str:
    if source_context_ref_count > 0 and evaluation_status != "PASSED":
        raise Stage6Error(422, "PROVIDER_OUTPUT_INVALID", "Stage 6 replay requires passed source evaluation evidence.")
    expected = build_source_evaluation_checksum(
        source_evaluation_id=source_evaluation_id,
        source_run_id=source_run_id,
        trace_id=trace_id,
        evaluation_status=evaluation_status,
        source_context_ref_ids=source_context_ref_ids,
        source_context_ref_count=source_context_ref_count,
        source_citation_indexes=source_citation_indexes,
        source_citation_count=source_citation_count,
    )
    if source_evaluation_checksum != expected:
        raise Stage6Error(422, "PROVIDER_OUTPUT_INVALID", "Source evaluation checksum is invalid.")
    return expected


def validate_multilingual_source_evidence(
    *,
    source_text: str,
    evaluation_status: EvaluationStatus,
    source_evaluation_checksum_supplied: bool,
    source_context_ref_count: int,
    source_citation_count: int,
    source_context_ref_ids: tuple[str, ...],
    source_citation_indexes: tuple[int, ...],
    source_claim_support_ids: tuple[str, ...],
) -> None:
    if evaluation_status != "PASSED":
        raise Stage6Error(
            422,
            "PROVIDER_OUTPUT_INVALID",
            "Stage 6 requires passed source evaluation evidence.",
        )
    if not source_evaluation_checksum_supplied:
        raise Stage6Error(
            422,
            "PROVIDER_OUTPUT_INVALID",
            "Stage 6 requires an explicit source evaluation checksum.",
        )
    markers = citation_marker_sequence(source_text)
    if not markers:
        raise Stage6Error(
            422,
            "TRANSCRIPT_CORRECTNESS_FAILED",
            "Source English text must include citation markers before multilingual generation.",
        )
    source_transcript_segments(source_text)
    if (
        source_context_ref_count <= 0
        or source_citation_count <= 0
        or not source_context_ref_ids
        or not source_citation_indexes
        or not source_claim_support_ids
        or source_citation_count != len(markers)
        or len(source_citation_indexes) != len(markers)
        or len(source_claim_support_ids) != len(markers)
    ):
        raise Stage6Error(
            422,
            "PROVIDER_OUTPUT_INVALID",
            "Stage 6 requires source citation, context, and claim-support evidence.",
        )


def restored_voice_manifest_matches(
    *,
    voice_manifest: dict[str, Any],
    translation_provider: dict[str, Any],
    source_language: str,
    target_language: str,
    voice: dict[str, Any],
    voice_provider_id: str,
    voice_provider_mode: ProviderMode,
    translated_script_text: str,
    source_run_id: str,
    trace_id: str,
    actor_id: str,
    source_evaluation_id: str,
    source_evaluation_checksum: str,
    evaluation_status: EvaluationStatus,
    source_context_ref_count: int,
    source_context_ref_ids: tuple[str, ...],
    source_citation_count: int,
    source_citation_indexes: tuple[int, ...],
    source_claim_support_ids: tuple[str, ...],
    audio_artifact: DownloadableArtifact | None,
) -> bool:
    if (
        normalize_language_tag(str(translation_provider["source_language"])) != source_language
        or normalize_language_tag(str(translation_provider["target_language"])) != target_language
        or normalize_language_tag(str(voice["language"])) != target_language
        or str(voice_manifest["textChecksum"]) != checksum_text(translated_script_text)
        or normalize_language_tag(str(voice_manifest["language"])) != target_language
        or str(voice_manifest["provider"]) != voice_provider_id
        or validate_provider_mode(str(voice_manifest["providerMode"])) != voice_provider_mode
    ):
        return False
    if voice_manifest.get("schemaVersion") != "stage6-tts-manifest-v2":
        return True
    return (
        str(voice_manifest["sourceRunId"]) == source_run_id
        and str(voice_manifest["traceId"]) == trace_id
        and str(voice_manifest["audienceId"]) == actor_id
        and str(voice_manifest["sourceEvaluationId"]) == source_evaluation_id
        and str(voice_manifest["sourceEvaluationChecksum"]) == source_evaluation_checksum
        and str(voice_manifest["sourceEvaluationStatus"]) == evaluation_status
        and int(voice_manifest["sourceContextRefCount"]) == source_context_ref_count
        and tuple(str(value) for value in voice_manifest["sourceContextRefIds"]) == source_context_ref_ids
        and int(voice_manifest["sourceCitationCount"]) == source_citation_count
        and tuple(int(value) for value in voice_manifest["sourceCitationIndexes"]) == source_citation_indexes
        and tuple(str(value) for value in voice_manifest["sourceClaimSupportIds"]) == source_claim_support_ids
        and voice_manifest["citationMarkers"] == citation_marker_sequence(translated_script_text)
        and audio_artifact is not None
        and str(voice_manifest["artifactChecksum"]) == audio_artifact.checksum
        and str(voice_manifest["artifactMimeType"]) == audio_artifact.mime_type
    )


def validate_stage6_scope(
    *,
    idempotency_scope: str,
    tenant_id: str,
    project_id: str,
    actor_id: str,
    source_run_id: str,
) -> None:
    scope_parts = idempotency_scope.split(":")
    if len(scope_parts) != 4:
        raise Stage6Error(422, "PROVIDER_OUTPUT_INVALID", "Stage 6 idempotency scope is invalid.")
    scope_tenant_id, scope_actor_id, scope_project_id, scope_source_run_id = scope_parts
    if scope_source_run_id == "run":
        scope_source_run_id = source_run_id
    if (
        scope_tenant_id != tenant_id
        or scope_actor_id != actor_id
        or scope_project_id != project_id
        or scope_source_run_id != source_run_id
    ):
        raise Stage6Error(
            422,
            "PROVIDER_OUTPUT_INVALID",
            "Stage 6 idempotency scope does not match the source binding.",
        )


def validate_provider_id(provider: str, *, field_name: str) -> str:
    candidate = provider.strip().lower()
    if not PROVIDER_ID_PATTERN.fullmatch(candidate):
        raise Stage6Error(422, "PROVIDER_OUTPUT_INVALID", f"Invalid {field_name} identifier.")
    return candidate


def validate_provider_mode(provider_mode: str) -> ProviderMode:
    candidate = provider_mode.strip().upper()
    if candidate not in {"LOCAL", "DISABLED", "OPTIONAL_EXTERNAL"}:
        raise Stage6Error(422, "PROVIDER_OUTPUT_INVALID", "Invalid provider mode.")
    return cast(ProviderMode, candidate)


def validate_local_provider_mode(provider_mode: str, *, field_name: str) -> ProviderMode:
    candidate = validate_provider_mode(provider_mode)
    if candidate != "LOCAL":
        raise Stage6Error(422, "PROVIDER_OUTPUT_INVALID", f"{field_name} must be local.")
    return candidate


def validate_voice_fallback_reason(fallback_reason: str | None) -> str | None:
    if fallback_reason is None:
        return None
    candidate = fallback_reason.strip().upper()
    if candidate != "REQUESTED_PROVIDER_UNAVAILABLE":
        raise Stage6Error(422, "PROVIDER_OUTPUT_INVALID", "Invalid voice provider fallback reason.")
    return candidate


def validate_downloadable_artifact(
    artifact: DownloadableArtifact,
    *,
    expected_mime_type: str,
    expected_extension: str,
) -> DownloadableArtifact:
    if artifact.mime_type != expected_mime_type:
        raise Stage6Error(422, "PROVIDER_OUTPUT_INVALID", "Downloadable artifact MIME type is invalid.")
    if not artifact.file_name.endswith(expected_extension) or not is_safe_artifact_filename(artifact.file_name):
        raise Stage6Error(422, "PROVIDER_OUTPUT_INVALID", "Downloadable artifact filename is invalid.")
    try:
        decoded = _decode_artifact_content(artifact.content_base64, field_name="Downloadable artifact")
    except Stage6Error:
        raise
    except (binascii.Error, TypeError, UnicodeDecodeError) as exc:
        raise Stage6Error(422, "PROVIDER_OUTPUT_INVALID", "Downloadable artifact content is invalid.") from exc
    if artifact.checksum != checksum_text(decoded):
        raise Stage6Error(422, "PROVIDER_OUTPUT_INVALID", "Downloadable artifact checksum is invalid.")
    return artifact


def validate_voice_manifest_artifact(artifact: DownloadableArtifact) -> DownloadableArtifact:
    if artifact.mime_type != "application/json":
        raise Stage6Error(422, "PROVIDER_OUTPUT_INVALID", "Voice provider artifact must be a JSON manifest.")
    if not artifact.file_name.endswith(".json") or not is_safe_artifact_filename(artifact.file_name):
        raise Stage6Error(422, "PROVIDER_OUTPUT_INVALID", "Voice provider artifact filename is invalid.")
    try:
        decoded = _decode_artifact_content(artifact.content_base64, field_name="Voice provider artifact")
        parsed = json.loads(decoded)
    except Stage6Error:
        raise
    except (binascii.Error, TypeError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise Stage6Error(422, "PROVIDER_OUTPUT_INVALID", "Voice provider artifact must contain valid JSON.") from exc
    if not isinstance(parsed, dict):
        raise Stage6Error(422, "PROVIDER_OUTPUT_INVALID", "Voice provider manifest must be a JSON object.")
    if set(parsed) != VOICE_MANIFEST_KEYS:
        raise Stage6Error(422, "PROVIDER_OUTPUT_INVALID", "Voice provider manifest schema is invalid.")
    if parsed["provider"] != "mock":
        raise Stage6Error(422, "PROVIDER_OUTPUT_INVALID", "Voice provider manifest provider is invalid.")
    validate_local_provider_mode(str(parsed["providerMode"]), field_name="voice provider manifest provider mode")
    normalize_language_tag(str(parsed["language"]))
    if not isinstance(parsed["languageDisplayName"], str) or not parsed["languageDisplayName"].strip():
        raise Stage6Error(422, "PROVIDER_OUTPUT_INVALID", "Voice provider manifest language display name is invalid.")
    if not isinstance(parsed["textChecksum"], str) or not parsed["textChecksum"].startswith("sha256:"):
        raise Stage6Error(422, "PROVIDER_OUTPUT_INVALID", "Voice provider manifest text checksum is invalid.")
    duration_estimate = parsed["durationSecondsEstimate"]
    if not isinstance(duration_estimate, int | float) or duration_estimate <= 0:
        raise Stage6Error(422, "PROVIDER_OUTPUT_INVALID", "Voice provider manifest duration is invalid.")
    audio_profile = parsed["mockAudioProfile"]
    if not isinstance(audio_profile, dict) or set(audio_profile) != MOCK_AUDIO_PROFILE_KEYS:
        raise Stage6Error(422, "PROVIDER_OUTPUT_INVALID", "Voice provider manifest audio profile schema is invalid.")
    if audio_profile["sampleRateHz"] != 16000 or audio_profile["channels"] != 1:
        raise Stage6Error(422, "PROVIDER_OUTPUT_INVALID", "Voice provider manifest audio profile is invalid.")
    profile_duration = audio_profile["durationMillisecondsEstimate"]
    if not isinstance(profile_duration, int) or profile_duration <= 0:
        raise Stage6Error(422, "PROVIDER_OUTPUT_INVALID", "Voice provider manifest audio duration is invalid.")
    if not isinstance(parsed["disclosure"], str) or "Mock local TTS placeholder" not in parsed["disclosure"]:
        raise Stage6Error(422, "PROVIDER_OUTPUT_INVALID", "Voice provider manifest disclosure is invalid.")
    if artifact.checksum != checksum_text(decoded):
        raise Stage6Error(422, "PROVIDER_OUTPUT_INVALID", "Voice provider artifact checksum is invalid.")
    return artifact


def is_tts_manifest_artifact(artifact: DownloadableArtifact) -> bool:
    if artifact.mime_type != "application/json":
        return False
    try:
        parsed = json.loads(artifact_text(artifact))
    except (Stage6Error, json.JSONDecodeError):
        return False
    return isinstance(parsed, dict) and parsed.get("schemaVersion") == "stage6-tts-manifest-v2"


def validate_tts_manifest_artifact(artifact: DownloadableArtifact) -> DownloadableArtifact:
    if artifact.mime_type != "application/json":
        raise Stage6Error(422, "PROVIDER_OUTPUT_INVALID", "TTS manifest must be JSON.")
    if not artifact.file_name.endswith(".json") or not is_safe_artifact_filename(artifact.file_name):
        raise Stage6Error(422, "PROVIDER_OUTPUT_INVALID", "TTS manifest filename is invalid.")
    decoded = artifact_text(artifact)
    try:
        parsed = json.loads(decoded)
    except json.JSONDecodeError as exc:
        raise Stage6Error(422, "PROVIDER_OUTPUT_INVALID", "TTS manifest must contain valid JSON.") from exc
    if not isinstance(parsed, dict):
        raise Stage6Error(422, "PROVIDER_OUTPUT_INVALID", "TTS manifest must be a JSON object.")
    required_keys = {
        "schemaVersion",
        "provider",
        "providerMode",
        "requestedProvider",
        "fallbackReason",
        "language",
        "languageDisplayName",
        "textChecksum",
        "sourceRunId",
        "traceId",
        "audienceId",
        "sourceContextRefCount",
        "sourceContextRefIds",
        "sourceCitationCount",
        "sourceCitationIndexes",
        "sourceClaimSupportIds",
        "sourceEvaluationId",
        "sourceEvaluationStatus",
        "sourceEvaluationChecksum",
        "citationMarkers",
        "providerModelId",
        "providerModelVersion",
        "providerHistoryItemId",
        "voiceProvenance",
        "artifactChecksum",
        "artifactMimeType",
        "estimatedBillableCharacters",
        "attemptCount",
        "disclosure",
    }
    if set(parsed) != required_keys:
        raise Stage6Error(422, "PROVIDER_OUTPUT_INVALID", "TTS manifest schema is invalid.")
    if parsed["schemaVersion"] != "stage6-tts-manifest-v2":
        raise Stage6Error(422, "PROVIDER_OUTPUT_INVALID", "TTS manifest schema version is invalid.")
    validate_provider_id(str(parsed["provider"]), field_name="TTS manifest provider")
    validate_provider_mode(str(parsed["providerMode"]))
    validate_provider_id(str(parsed["requestedProvider"]), field_name="TTS requested provider")
    normalize_language_tag(str(parsed["language"]))
    if parsed["voiceProvenance"] != "stock":
        raise Stage6Error(422, "PROVIDER_OUTPUT_INVALID", "TTS manifest voice provenance is invalid.")
    if str(parsed["artifactMimeType"]) not in SUPPORTED_AUDIO_MIME_TYPES:
        raise Stage6Error(422, "PROVIDER_OUTPUT_INVALID", "TTS manifest artifact MIME type is invalid.")
    if not str(parsed["artifactChecksum"]).startswith("sha256:"):
        raise Stage6Error(422, "PROVIDER_OUTPUT_INVALID", "TTS manifest artifact checksum is invalid.")
    if artifact.checksum != checksum_text(decoded):
        raise Stage6Error(422, "PROVIDER_OUTPUT_INVALID", "TTS manifest checksum is invalid.")
    return artifact


def validate_audio_artifact(artifact: DownloadableArtifact) -> DownloadableArtifact:
    if artifact.mime_type not in SUPPORTED_AUDIO_MIME_TYPES:
        raise Stage6Error(422, "PROVIDER_OUTPUT_INVALID", "TTS audio MIME type is invalid.")
    expected_extension = SUPPORTED_AUDIO_MIME_TYPES[artifact.mime_type]
    if not artifact.file_name.endswith(expected_extension) or not is_safe_artifact_filename(artifact.file_name):
        raise Stage6Error(422, "PROVIDER_OUTPUT_INVALID", "TTS audio filename is invalid.")
    if len(artifact.content_base64) > MAX_STAGE6_ARTIFACT_BASE64_CHARS:
        raise Stage6Error(413, "PROVIDER_OUTPUT_TOO_LARGE", "TTS audio artifact exceeds the Stage 6 limit.")
    try:
        decoded = base64.b64decode(artifact.content_base64, validate=True)
    except (binascii.Error, TypeError) as exc:
        raise Stage6Error(422, "PROVIDER_OUTPUT_INVALID", "TTS audio artifact content is invalid.") from exc
    if len(decoded) > MAX_STAGE6_ARTIFACT_BYTES:
        raise Stage6Error(413, "PROVIDER_OUTPUT_TOO_LARGE", "TTS audio artifact exceeds the Stage 6 limit.")
    if artifact.checksum != checksum_bytes(decoded):
        raise Stage6Error(422, "PROVIDER_OUTPUT_INVALID", "TTS audio checksum is invalid.")
    return artifact


def is_safe_artifact_filename(file_name: str) -> bool:
    if not file_name or "/" in file_name or "\\" in file_name:
        return False
    return not any(ord(character) < 32 or ord(character) == 127 for character in file_name)


def protect_terms(text: str, glossary_terms: list[str]) -> tuple[str, dict[str, str]]:
    protected = text
    placeholders: dict[str, str] = {}
    for index, term in enumerate(sorted(glossary_terms, key=len, reverse=True), start=1):
        if term not in protected:
            continue
        placeholder = f"__NT_TERM_{index:03d}__"
        protected = protected.replace(term, placeholder)
        placeholders[placeholder] = term
    return protected, placeholders


def restore_terms(text: str, placeholders: dict[str, str]) -> str:
    restored = text
    for placeholder, term in placeholders.items():
        restored = restored.replace(placeholder, term)
    return restored


def generate_subtitles(
    *,
    script_text: str,
    language: str,
    seconds_per_caption: int = 4,
) -> str:
    normalize_language_tag(language)
    captions = split_captions(script_text)
    if len(captions) > MAX_CAPTION_COUNT:
        raise Stage6Error(422, "PROVIDER_OUTPUT_INVALID", "Translation provider output creates too many subtitles.")
    entries = []
    for index, caption in enumerate(captions, start=1):
        start = timedelta(seconds=(index - 1) * seconds_per_caption)
        end = timedelta(seconds=index * seconds_per_caption)
        entries.append(srt.Subtitle(index=index, start=start, end=end, content=caption))
    return cast(str, srt.compose(entries))


def split_captions(script_text: str) -> list[str]:
    sentences = [part.strip() for part in re.split(r"(?<=[.!?])\s+", script_text.strip()) if part.strip()]
    if not sentences:
        return []
    captions: list[str] = []
    for sentence in sentences:
        if len(sentence) <= MAX_CAPTION_CHARS:
            captions.append(sentence)
            continue
        words = sentence.split()
        current: list[str] = []
        for word in words:
            if len(word) > MAX_CAPTION_CHARS:
                if current:
                    captions.append(" ".join(current))
                    current = []
                captions.extend(split_long_token(word))
                continue
            candidate = " ".join([*current, word])
            if current and len(candidate) > MAX_CAPTION_CHARS:
                captions.append(" ".join(current))
                current = [word]
            else:
                current.append(word)
        if current:
            captions.append(" ".join(current))
    return captions


def split_long_token(token: str) -> list[str]:
    return [token[index : index + MAX_CAPTION_CHARS] for index in range(0, len(token), MAX_CAPTION_CHARS)]


def resolve_voice_provider(requested_provider: str) -> tuple[str, str | None]:
    normalized = validate_provider_id(requested_provider or "mock", field_name="requested voice provider")
    if normalized == "mock":
        return "mock", None
    if normalized == "elevenlabs":
        return "elevenlabs", None
    return normalized or "mock", "REQUESTED_PROVIDER_UNAVAILABLE"


def estimate_duration_seconds(text: str) -> int:
    word_count = len(text.split())
    return max(1, int(word_count / 2.4))


def language_display_name(language: str) -> str:
    normalized_language = normalize_language_tag(language)
    record = LANGUAGE_CATALOG_BY_TAG.get(normalized_language)
    if record is not None:
        return record.english_name
    return cast(str, Locale.parse(normalized_language).get_display_name("en"))


def mock_audio_profile(duration_seconds: int) -> dict[str, int]:
    duration_ms = max(1, duration_seconds) * 1000
    segment = AudioSegment.silent(duration=duration_ms, frame_rate=16_000).set_channels(1)
    return {
        "durationMillisecondsEstimate": len(segment),
        "sampleRateHz": segment.frame_rate,
        "channels": segment.channels,
    }


def artifact_from_text(*, file_name: str, mime_type: str, text: str) -> DownloadableArtifact:
    encoded = base64.b64encode(text.encode("utf-8")).decode("ascii")
    return DownloadableArtifact(
        file_name=file_name,
        mime_type=mime_type,
        content_base64=encoded,
        checksum=checksum_text(text),
    )


def artifact_from_bytes(*, file_name: str, mime_type: str, content: bytes) -> DownloadableArtifact:
    encoded = base64.b64encode(content).decode("ascii")
    return DownloadableArtifact(
        file_name=file_name,
        mime_type=mime_type,
        content_base64=encoded,
        checksum=checksum_bytes(content),
    )


def build_tts_manifest_text(
    *,
    provider_result: ExternalTTSResult,
    requested_provider: str,
    language: str,
    text: str,
    actor_id: str,
    source_run_id: str,
    trace_id: str,
    source_context_ref_count: int,
    source_context_ref_ids: tuple[str, ...],
    source_citation_count: int,
    source_citation_indexes: tuple[int, ...],
    source_claim_support_ids: tuple[str, ...],
    source_evaluation_id: str,
    source_evaluation_checksum: str,
    evaluation_status: EvaluationStatus,
    audio_artifact: DownloadableArtifact,
) -> str:
    payload = {
        "schemaVersion": "stage6-tts-manifest-v2",
        "provider": provider_result.provider,
        "providerMode": provider_result.provider_mode,
        "requestedProvider": requested_provider,
        "fallbackReason": None,
        "language": language,
        "languageDisplayName": language_display_name(language),
        "textChecksum": checksum_text(text),
        "sourceRunId": source_run_id,
        "traceId": trace_id,
        "audienceId": actor_id,
        "sourceContextRefCount": source_context_ref_count,
        "sourceContextRefIds": list(source_context_ref_ids),
        "sourceCitationCount": source_citation_count,
        "sourceCitationIndexes": list(source_citation_indexes),
        "sourceClaimSupportIds": list(source_claim_support_ids),
        "sourceEvaluationId": source_evaluation_id,
        "sourceEvaluationStatus": evaluation_status,
        "sourceEvaluationChecksum": source_evaluation_checksum,
        "citationMarkers": citation_marker_sequence(text),
        "providerModelId": provider_result.model_id,
        "providerModelVersion": provider_result.model_version,
        "providerHistoryItemId": provider_result.provider_history_item_id,
        "voiceProvenance": provider_result.voice_provenance,
        "artifactChecksum": audio_artifact.checksum,
        "artifactMimeType": audio_artifact.mime_type,
        "estimatedBillableCharacters": provider_result.estimated_billable_characters,
        "attemptCount": provider_result.attempt_count,
        "disclosure": "AI-generated TTS audio using a non-cloned stock voice. No cloned voice was used.",
    }
    return json.dumps(payload, sort_keys=True)


def build_stage6_metadata_text(
    *,
    multilingual_run_id: str,
    request_checksum: str,
    tenant_id: str,
    project_id: str,
    actor_id: str,
    source_run_id: str,
    trace_id: str,
    source_language: str,
    target_language: str,
    source_text_checksum: str,
    source_context_ref_count: int,
    source_context_ref_ids: tuple[str, ...],
    source_citation_count: int,
    source_citation_indexes: tuple[int, ...],
    source_claim_support_ids: tuple[str, ...],
    source_evaluation_id: str,
    source_evaluation_checksum: str,
    evaluation_status: EvaluationStatus,
    glossary_terms: list[str],
    preserved_terms: list[str],
    source_script_text: str,
    translated_script_text: str,
    transcript_segments: tuple[MultilingualTranscriptSegment, ...],
    transcript_correctness: TranscriptCorrectness,
    translation_provider: TranslationProviderResult,
    voice: VoiceProviderResult,
    translated_script_artifact: DownloadableArtifact,
    subtitles_artifact: DownloadableArtifact,
) -> str:
    payload = {
        "schemaVersion": "stage6-metadata-v1",
        "multilingualRunId": multilingual_run_id,
        "requestChecksum": request_checksum,
        "tenantId": tenant_id,
        "projectId": project_id,
        "actorId": actor_id,
        "sourceRunId": source_run_id,
        "traceId": trace_id,
        "sourceLanguage": source_language,
        "targetLanguage": target_language,
        "sourceScriptText": source_script_text,
        "sourceTextChecksum": source_text_checksum,
        "translatedScriptText": translated_script_text,
        "sourceContextRefCount": source_context_ref_count,
        "sourceContextRefIds": list(source_context_ref_ids),
        "sourceCitationCount": source_citation_count,
        "sourceCitationIndexes": list(source_citation_indexes),
        "sourceClaimSupportIds": list(source_claim_support_ids),
        "sourceEvaluationId": source_evaluation_id,
        "sourceEvaluationChecksum": source_evaluation_checksum,
        "evaluationStatus": evaluation_status,
        "glossaryTerms": glossary_terms,
        "preservedTerms": preserved_terms,
        "citationMarkers": sorted(citation_markers(source_script_text)),
        "transcriptCorrectness": transcript_correctness_to_api(transcript_correctness),
        "transcriptSegments": [transcript_segment_to_api(segment) for segment in transcript_segments],
        "translationProvider": {
            "provider": translation_provider.provider,
            "providerMode": translation_provider.provider_mode,
            "sourceLanguage": translation_provider.source_language,
            "targetLanguage": translation_provider.target_language,
            "translatedTextChecksum": checksum_text(translated_script_text),
        },
        "voiceProvider": {
            "provider": voice.provider,
            "providerMode": voice.provider_mode,
            "requestedProvider": voice.requested_provider,
            "fallbackReason": voice.fallback_reason,
            "language": voice.language,
            "artifactChecksum": voice.artifact.checksum,
            "audioArtifactChecksum": voice.audio_artifact.checksum if voice.audio_artifact is not None else None,
        },
        "artifacts": {
            "translatedScriptChecksum": translated_script_artifact.checksum,
            "subtitlesChecksum": subtitles_artifact.checksum,
            "voiceManifestChecksum": voice.artifact.checksum,
            "voiceAudioChecksum": voice.audio_artifact.checksum if voice.audio_artifact is not None else None,
        },
    }
    return json.dumps(payload, sort_keys=True)


def multilingual_to_api(result: MultilingualWalkthroughResult) -> dict[str, object]:
    artifacts: dict[str, object] = {
        "translatedScript": artifact_to_api(result.artifacts.translated_script),
        "subtitles": artifact_to_api(result.artifacts.subtitles),
        "voiceManifest": artifact_to_api(result.artifacts.voice_manifest),
        "metadata": artifact_to_api(result.artifacts.metadata),
    }
    if result.artifacts.voice_audio is not None:
        artifacts["voiceAudio"] = artifact_to_api(result.artifacts.voice_audio)
    return {
        "multilingualRunId": result.multilingual_run_id,
        "tenantId": result.tenant_id,
        "projectId": result.project_id,
        "actorId": result.actor_id,
        "sourceRunId": result.source_run_id,
        "sourceLanguage": result.source_language,
        "targetLanguage": result.target_language,
        "status": result.status,
        "sourceScriptText": result.source_script_text,
        "sourceTextChecksum": result.source_text_checksum,
        "translatedScriptText": result.translated_script_text,
        "subtitlesText": result.subtitles_text,
        "transcriptSegments": [transcript_segment_to_api(segment) for segment in result.transcript_segments],
        "transcriptCorrectness": transcript_correctness_to_api(result.transcript_correctness),
        "glossaryTerms": result.glossary_terms,
        "preservedTerms": result.preserved_terms,
        "translationProvider": {
            "provider": result.translation_provider.provider,
            "providerMode": result.translation_provider.provider_mode,
        },
        "voice": {
            "provider": result.voice.provider,
            "providerMode": result.voice.provider_mode,
            "requestedProvider": result.voice.requested_provider,
            "fallbackReason": result.voice.fallback_reason,
            "language": result.voice.language,
            "artifact": artifact_to_api(result.voice.artifact),
        },
        "artifacts": artifacts,
        "trace": {
            "traceId": result.trace_id,
            "tenantId": result.tenant_id,
            "projectId": result.project_id,
            "actorId": result.actor_id,
            "sourceRunId": result.source_run_id,
            "sourceLanguage": result.source_language,
            "targetLanguage": result.target_language,
            "sourceTextChecksum": result.source_text_checksum,
            "sourceContextRefCount": result.source_context_ref_count,
            "sourceCitationCount": result.source_citation_count,
            "sourceContextRefIds": list(result.source_context_ref_ids),
            "sourceCitationIndexes": list(result.source_citation_indexes),
            "sourceClaimSupportIds": list(result.source_claim_support_ids),
            "sourceEvaluationId": result.source_evaluation_id,
            "sourceEvaluationChecksum": result.source_evaluation_checksum,
            "evaluationStatus": result.evaluation_status,
        },
    }


def artifact_to_api(artifact: DownloadableArtifact) -> dict[str, str]:
    return {
        "fileName": artifact.file_name,
        "mimeType": artifact.mime_type,
        "contentBase64": artifact.content_base64,
        "checksum": artifact.checksum,
    }


stage6_service = create_stage6_service(state_path=resolve_state_file("stage6"))
