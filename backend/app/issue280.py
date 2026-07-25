"""Issue 280 PR B executable input/API/error contract slice."""

from __future__ import annotations

import base64
import html
import json
import re
from dataclasses import dataclass
from pathlib import PurePath
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from backend.app.rag.chunking import checksum_text
from backend.app.stage6 import LANGUAGE_CATALOG_BY_TAG, LanguageCatalogRecord
from backend.app.stage4 import contains_prompt_injection, contains_secret_like_content, normalize_content_type

ISSUE280_INPUT_CONTRACT_PATH = "/api/v1/checkpoint3/issue280/input-contract"
ISSUE280_LOCAL_E2E_DEMO_PATH = "/api/v1/checkpoint3/issue280/local-e2e-demo"
ISSUE280_CONTRACT_VERSION = "issue280-input-api-error-v1"
ISSUE280_LOCAL_E2E_CONTRACT_VERSION = "issue280-local-e2e-demo-v1"
ISSUE280_MAX_BYTES = 20_000
ISSUE280_MAX_DOCUMENTS = 3
ISSUE280_MAX_SECTIONS_PER_DOCUMENT = 12
ISSUE280_MAX_BODY_CHARS_PER_SECTION = 2_000
ISSUE280_MAX_TRANSCRIPT_SEGMENTS = 40
ISSUE280_MAX_GLOSSARY_TERMS = 20
ISSUE280_MAX_GLOSSARY_TERM_CHARS = 64
ISSUE280_MAX_CAPTION_CHARS = 240
ISSUE280_MAX_EXPORT_BUNDLE_BYTES = 1_000_000

_MARKDOWN_CONTENT_TYPE = "text/markdown"
_HEADING_PATTERN = re.compile(r"^#{1,6}\s+\S", re.MULTILINE)
_CONTROL_CHARACTER_PATTERN = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")
_PRIVATE_MARKER_PATTERN = re.compile(
    r"\b(confidential|do not share|internal only|private key|social security|ssn)\b",
    re.IGNORECASE,
)
_GLOSSARY_INSTRUCTION_PATTERN = re.compile(
    r"\b(ignore|translate|rewrite|casual|casually|citation|citations|source|sources|"
    r"instruction|instructions|audience|depth|language|prompt|developer|system)\b",
    re.IGNORECASE,
)
_SUPPORTED_LOCAL_E2E_LANGUAGES = {
    record.language_tag: record
    for record in LANGUAGE_CATALOG_BY_TAG.values()
    if record.local_demo_support_status == "SUPPORTED"
    and record.provider_support_status == "LOCAL_DEMO_FIXTURE"
    and record.test_coverage_level == "CHECKPOINT3A_EXHAUSTIVE"
}
_SENTENCE_PATTERN = re.compile(r"^(?P<claim>.+?)\s*\[(?P<citation>\d+)\]\.?$")
_AUDIENCE_PROFILES = {
    "RECRUITER": ("recruiters", "hiring signal"),
    "HIRING_MANAGER": ("hiring managers", "delivery confidence"),
    "ENGINEER": ("engineers", "implementation evidence"),
    "PRODUCT_LEADER": ("product leaders", "portfolio narrative"),
    "CUSTOMER": ("customers", "customer value"),
    "BEGINNER": ("beginners", "plain-language orientation"),
    "GLOBAL_VIEWER": ("global viewers", "globally understandable context"),
}
_LOCAL_TRANSLATION_TEMPLATES = {
    "accepts_public_safe_markdown": "{term} accepts bounded public-safe markdown from project teams{citation}",
    "extracts_source_backed_claims": "The local demo extracts source-backed claims about release rituals, adoption signals, and evidence handoffs for {term}{citation}",
    "refuses_unsupported_claims": "{term} refuses unsupported claims before the stored walkthrough is shown in the browser{citation}",
    "preserves_artifact_evidence": "Local demo artifacts for {term} preserve citations, context references, claim supports, and checksums in alignment{citation}",
    "links_adoption_evidence": "The workspace for {term} links adoption metrics and release blockers to cited markdown sections{citation}",
    "explains_adoption_safety_handoffs": "{term} explains adoption metrics, safety gates, and reviewer handoffs{citation}",
    "source_backed_example": "Source-backed example: {term} links weekly adoption metrics to cited release review sections{citation}",
    "review_tradeoff": "Source-backed benefit and tradeoff: cited release reviews improve traceability but add reviewer effort for {term}{citation}",
    "weekly_review_way_forward": "Way forward: review release blockers weekly before sharing the {term} walkthrough{citation}",
}
_LOCAL_SEMANTIC_TRANSLATIONS = {
    "hi": {
        "accepts_public_safe_markdown": "{term} लॉन्च टीमों से सीमित सार्वजनिक-सुरक्षित मार्कडाउन स्वीकार करता है{citation}",
        "extracts_source_backed_claims": "{term} में स्थानीय डेमो रिलीज़ रीति-रिवाज, अपनाने के संकेत और प्रमाण हैंडऑफ़ पर स्रोत-समर्थित दावे निकालता है{citation}",
        "refuses_unsupported_claims": "{term} संग्रहीत वॉकथ्रू ब्राउज़र में दिखाने से पहले असमर्थित दावों को अस्वीकार करता है{citation}",
        "preserves_artifact_evidence": "{term} के स्थानीय डेमो आर्टिफैक्ट उद्धरण, संदर्भ रेफ, दावा समर्थन और चेकसम मिलाकर रखते हैं{citation}",
        "links_adoption_evidence": "{term} का कार्यक्षेत्र अपनाने के मेट्रिक और रिलीज़ अवरोधों को उद्धृत मार्कडाउन खंडों से जोड़ता है{citation}",
        "explains_adoption_safety_handoffs": "{term} अपनाने के मेट्रिक, सुरक्षा गेट और समीक्षक हैंडऑफ़ समझाता है{citation}",
        "source_backed_example": "स्रोत-समर्थित उदाहरण: {term} साप्ताहिक अपनाने के मेट्रिक को उद्धृत रिलीज़ समीक्षा खंडों से जोड़ता है{citation}",
        "review_tradeoff": "स्रोत-समर्थित लाभ और समझौता: उद्धृत रिलीज़ समीक्षाएँ पता लगाने योग्य प्रमाण बेहतर बनाती हैं, लेकिन {term} के लिए समीक्षक प्रयास बढ़ाती हैं{citation}",
        "weekly_review_way_forward": "आगे का रास्ता: {term} वॉकथ्रू साझा करने से पहले रिलीज़ अवरोधों की साप्ताहिक समीक्षा करें{citation}",
    },
    "es": {
        "accepts_public_safe_markdown": "{term} acepta markdown publico seguro y acotado de los equipos de lanzamiento{citation}",
        "extracts_source_backed_claims": "La demo local de {term} extrae afirmaciones respaldadas por fuentes sobre rituales de lanzamiento, senales de adopcion y traspasos de evidencia{citation}",
        "refuses_unsupported_claims": "{term} rechaza afirmaciones sin respaldo antes de mostrar el recorrido guardado en el navegador{citation}",
        "preserves_artifact_evidence": "Los artefactos de demo local de {term} conservan citas, referencias de contexto, soportes de afirmaciones y sumas de verificacion alineadas{citation}",
        "links_adoption_evidence": "El espacio de trabajo de {term} vincula metricas de adopcion y bloqueos de lanzamiento con secciones markdown citadas{citation}",
        "explains_adoption_safety_handoffs": "{term} explica metricas de adopcion, controles de seguridad y traspasos de revisores{citation}",
        "source_backed_example": "Ejemplo respaldado por la fuente: {term} vincula metricas semanales de adopcion con secciones citadas de revision de lanzamientos{citation}",
        "review_tradeoff": "Beneficio y contrapartida respaldados por la fuente: las revisiones de lanzamiento citadas mejoran la trazabilidad, pero agregan esfuerzo de revision para {term}{citation}",
        "weekly_review_way_forward": "Siguiente paso: revisar semanalmente los bloqueos de lanzamiento antes de compartir el recorrido de {term}{citation}",
    },
    "de": {
        "accepts_public_safe_markdown": "{term} akzeptiert begrenzte offentlich sichere Markdown-Inhalte von Launch-Teams{citation}",
        "extracts_source_backed_claims": "Die lokale Demo von {term} extrahiert quellengestutzte Aussagen zu Release-Ritualen, Nutzungssignalen und Evidenz-Ubergaben{citation}",
        "refuses_unsupported_claims": "{term} lehnt nicht gestutzte Aussagen ab, bevor der gespeicherte Walkthrough im Browser angezeigt wird{citation}",
        "preserves_artifact_evidence": "Lokale Demo-Artefakte von {term} bewahren Zitate, Kontextreferenzen, Claim-Supports und Prufsummen ausgerichtet auf{citation}",
        "links_adoption_evidence": "Der Arbeitsbereich von {term} verknupft Adoptionsmetriken und Release-Blocker mit zitierten Markdown-Abschnitten{citation}",
        "explains_adoption_safety_handoffs": "{term} erklart Adoptionsmetriken, Sicherheitsgates und Reviewer-Ubergaben{citation}",
    },
    "fr": {
        "accepts_public_safe_markdown": "{term} accepte un markdown public sur et limite des equipes de lancement{citation}",
        "extracts_source_backed_claims": "La demo locale de {term} extrait des affirmations appuyees par les sources sur les rituels de lancement, les signaux d'adoption et les passages de preuve{citation}",
        "refuses_unsupported_claims": "{term} refuse les affirmations non etayees avant d'afficher le parcours stocke dans le navigateur{citation}",
        "preserves_artifact_evidence": "Les artefacts de demo locale de {term} conservent les citations, references de contexte, supports d'affirmation et sommes de controle alignes{citation}",
        "links_adoption_evidence": "L'espace de travail de {term} relie les metriques d'adoption et les bloqueurs de livraison aux sections markdown citees{citation}",
        "explains_adoption_safety_handoffs": "{term} explique les metriques d'adoption, les controles de securite et les passages de relais des reviewers{citation}",
    },
    "pt-BR": {
        "accepts_public_safe_markdown": "{term} aceita markdown publico seguro e delimitado das equipes de lancamento{citation}",
        "extracts_source_backed_claims": "A demo local de {term} extrai afirmacoes baseadas em fonte sobre rituais de lancamento, sinais de adocao e passagens de evidencia{citation}",
        "refuses_unsupported_claims": "{term} recusa afirmacoes sem suporte antes de mostrar o passo a passo armazenado no navegador{citation}",
        "preserves_artifact_evidence": "Os artefatos da demo local de {term} preservam citacoes, referencias de contexto, suportes de afirmacoes e checksums alinhados{citation}",
        "links_adoption_evidence": "O espaco de trabalho de {term} vincula metricas de adocao e bloqueios de lancamento a secoes markdown citadas{citation}",
        "explains_adoption_safety_handoffs": "{term} explica metricas de adocao, gates de seguranca e repasses de revisores{citation}",
    },
    "it": {
        "accepts_public_safe_markdown": "{term} accetta markdown pubblico sicuro e limitato dai team di lancio{citation}",
        "extracts_source_backed_claims": "La demo locale di {term} estrae affermazioni supportate da fonti su rituali di rilascio, segnali di adozione e passaggi di evidenza{citation}",
        "refuses_unsupported_claims": "{term} rifiuta affermazioni non supportate prima che il walkthrough salvato sia mostrato nel browser{citation}",
        "preserves_artifact_evidence": "Gli artefatti della demo locale di {term} preservano citazioni, riferimenti di contesto, supporti alle affermazioni e checksum allineati{citation}",
        "links_adoption_evidence": "Lo spazio di lavoro di {term} collega metriche di adozione e blocchi di rilascio alle sezioni markdown citate{citation}",
        "explains_adoption_safety_handoffs": "{term} spiega metriche di adozione, gate di sicurezza e passaggi dei revisori{citation}",
    },
    "nl": {
        "accepts_public_safe_markdown": "{term} accepteert begrensde publiek veilige markdown van lanceringsteams{citation}",
        "extracts_source_backed_claims": "De lokale demo van {term} haalt brononderbouwde claims op over release-rituelen, adoptiesignalen en bewijs-overdrachten{citation}",
        "refuses_unsupported_claims": "{term} weigert niet-onderbouwde claims voordat de opgeslagen walkthrough in de browser wordt getoond{citation}",
        "preserves_artifact_evidence": "Lokale demo-artefacten van {term} bewaren citaties, contextreferenties, claimondersteuning en checksums in lijn{citation}",
        "links_adoption_evidence": "De werkruimte van {term} koppelt adoptiestatistieken en releaseblokkades aan geciteerde markdown-secties{citation}",
        "explains_adoption_safety_handoffs": "{term} legt adoptiestatistieken, veiligheidspoorten en reviewer-overdrachten uit{citation}",
    },
    "pl": {
        "accepts_public_safe_markdown": "{term} przyjmuje ograniczony publicznie bezpieczny markdown od zespolow wydan{citation}",
        "extracts_source_backed_claims": "Lokalne demo {term} wyodrebnia twierdzenia oparte na zrodlach o rytualach wydan, sygnalach adopcji i przekazaniach dowodow{citation}",
        "refuses_unsupported_claims": "{term} odrzuca niepoparte twierdzenia zanim zapisany walkthrough pojawi sie w przegladarce{citation}",
        "preserves_artifact_evidence": "Lokalne artefakty demo {term} zachowuja cytaty, referencje kontekstu, wsparcie twierdzen i zgodne sumy kontrolne{citation}",
        "links_adoption_evidence": "Obszar roboczy {term} laczy metryki adopcji i blokady wydan z cytowanymi sekcjami markdown{citation}",
        "explains_adoption_safety_handoffs": "{term} wyjasnia metryki adopcji, bramki bezpieczenstwa i przekazania recenzentow{citation}",
    },
    "uk": {
        "accepts_public_safe_markdown": "{term} приймає обмежений публічно безпечний markdown від команд запуску{citation}",
        "extracts_source_backed_claims": "Локальна демо {term} витягує підтверджені джерелами твердження про ритуали релізу, сигнали впровадження та передачу доказів{citation}",
        "refuses_unsupported_claims": "{term} відхиляє непідтверджені твердження до показу збереженого walkthrough у браузері{citation}",
        "preserves_artifact_evidence": "Локальні демо-артефакти {term} зберігають цитати, контекстні посилання, підтримку тверджень і узгоджені контрольні суми{citation}",
        "links_adoption_evidence": "Робочий простір {term} пов'язує метрики впровадження і блокери релізу з цитованими markdown-розділами{citation}",
        "explains_adoption_safety_handoffs": "{term} пояснює метрики впровадження, ворота безпеки та передачі рецензентів{citation}",
    },
    "ru": {
        "accepts_public_safe_markdown": "{term} принимает ограниченный публично безопасный markdown от команд запуска{citation}",
        "extracts_source_backed_claims": "Локальная демо {term} извлекает подтвержденные источниками утверждения о ритуалах релиза, сигналах внедрения и передаче доказательств{citation}",
        "refuses_unsupported_claims": "{term} отклоняет неподтвержденные утверждения до показа сохраненного walkthrough в браузере{citation}",
        "preserves_artifact_evidence": "Локальные демо-артефакты {term} сохраняют цитаты, контекстные ссылки, поддержку утверждений и согласованные контрольные суммы{citation}",
        "links_adoption_evidence": "Рабочая область {term} связывает метрики внедрения и блокеры релиза с цитированными markdown-разделами{citation}",
        "explains_adoption_safety_handoffs": "{term} объясняет метрики внедрения, ворота безопасности и передачи рецензентов{citation}",
    },
    "zh-Hans": {
        "accepts_public_safe_markdown": "{term} 接受来自发布团队的有界公共安全 Markdown{citation}",
        "extracts_source_backed_claims": "{term} 的本地演示提取关于发布仪式、采用信号和证据交接的来源支撑声明{citation}",
        "refuses_unsupported_claims": "{term} 在浏览器显示已存储演示前拒绝无支撑声明{citation}",
        "preserves_artifact_evidence": "{term} 的本地演示制品保留引用、上下文引用、声明支撑和校验和对齐{citation}",
        "links_adoption_evidence": "{term} 工作区把采用指标和发布阻碍链接到已引用的 Markdown 章节{citation}",
        "explains_adoption_safety_handoffs": "{term} 说明采用指标、安全门和评审交接{citation}",
    },
    "zh-Hant": {
        "accepts_public_safe_markdown": "{term} 接受來自發布團隊的有界公共安全 Markdown{citation}",
        "extracts_source_backed_claims": "{term} 的本地示範擷取關於發布儀式、採用訊號和證據交接的來源支撐聲明{citation}",
        "refuses_unsupported_claims": "{term} 在瀏覽器顯示已儲存 walkthrough 前拒絕無支撐聲明{citation}",
        "preserves_artifact_evidence": "{term} 的本地示範成品保留引用、情境參照、聲明支撐和校驗和對齊{citation}",
        "links_adoption_evidence": "{term} 工作區把採用指標和發布阻礙連結到已引用的 Markdown 章節{citation}",
        "explains_adoption_safety_handoffs": "{term} 說明採用指標、安全閘門和審閱交接{citation}",
    },
    "ja": {
        "accepts_public_safe_markdown": "{term} はローンチチームから限定された公開安全なMarkdownを受け付けます{citation}",
        "extracts_source_backed_claims": "{term} のローカルデモは、リリース儀式、採用シグナル、証拠引き継ぎに関するソース根拠付きの主張を抽出します{citation}",
        "refuses_unsupported_claims": "{term} は保存済みウォークスルーをブラウザに表示する前に、根拠のない主張を拒否します{citation}",
        "preserves_artifact_evidence": "{term} のローカルデモ成果物は、引用、コンテキスト参照、主張サポート、チェックサムの整合を保持します{citation}",
        "links_adoption_evidence": "{term} のワークスペースは、採用指標とリリース阻害要因を引用済みMarkdownセクションへ結び付けます{citation}",
        "explains_adoption_safety_handoffs": "{term} は採用指標、安全ゲート、レビュー担当者の引き継ぎを説明します{citation}",
    },
    "ko": {
        "accepts_public_safe_markdown": "{term}는 출시 팀의 제한된 공개 안전 Markdown을 받습니다{citation}",
        "extracts_source_backed_claims": "{term}의 로컬 데모는 릴리스 의식, 채택 신호, 증거 인계에 대한 출처 기반 주장을 추출합니다{citation}",
        "refuses_unsupported_claims": "{term}는 저장된 워크스루가 브라우저에 표시되기 전에 근거 없는 주장을 거부합니다{citation}",
        "preserves_artifact_evidence": "{term}의 로컬 데모 산출물은 인용, 컨텍스트 참조, 주장 근거, 체크섬 정렬을 보존합니다{citation}",
        "links_adoption_evidence": "{term} 작업공간은 채택 지표와 릴리스 차단요인을 인용된 Markdown 섹션에 연결합니다{citation}",
        "explains_adoption_safety_handoffs": "{term}는 채택 지표, 안전 게이트, 검토자 인계를 설명합니다{citation}",
    },
    "ar": {
        "accepts_public_safe_markdown": "{term} يقبل ماركداون عام آمن ومحدود من فرق الإطلاق{citation}",
        "extracts_source_backed_claims": "يعرض {term} محلياً ادعاءات مدعومة بالمصادر عن طقوس الإصدار وإشارات التبني وتسليم الأدلة{citation}",
        "refuses_unsupported_claims": "{term} يرفض الادعاءات غير المدعومة قبل عرض الجولة المخزنة في المتصفح{citation}",
        "preserves_artifact_evidence": "تحافظ آثار العرض المحلي في {term} على الاقتباسات ومراجع السياق ودعم الادعاءات والمجاميع الاختبارية متوافقة{citation}",
        "links_adoption_evidence": "تربط مساحة عمل {term} مقاييس التبني ومعوقات الإصدار بأقسام ماركداون مقتبسة{citation}",
        "explains_adoption_safety_handoffs": "{term} يشرح مقاييس التبني وبوابات السلامة وتسليمات المراجعين{citation}",
    },
    "arz": {
        "accepts_public_safe_markdown": "{term} بيقبل ماركداون عام آمن ومحدود من فرق الإطلاق{citation}",
        "extracts_source_backed_claims": "الديمو المحلي في {term} بيستخرج ادعاءات مسنودة بمصادر عن طقوس الإصدار وإشارات التبني وتسليم الأدلة{citation}",
        "refuses_unsupported_claims": "{term} بيرفض الادعاءات غير المسنودة قبل عرض الجولة المخزنة في المتصفح{citation}",
        "preserves_artifact_evidence": "آثار الديمو المحلي في {term} بتحافظ على الاقتباسات ومراجع السياق ودعم الادعاءات والمجاميع الاختبارية متوافقة{citation}",
        "links_adoption_evidence": "مساحة عمل {term} بتربط مقاييس التبني ومعوقات الإصدار بأقسام ماركداون مقتبسة{citation}",
        "explains_adoption_safety_handoffs": "{term} بيشرح مقاييس التبني وبوابات السلامة وتسليمات المراجعين{citation}",
    },
    "he": {
        "accepts_public_safe_markdown": "{term} מקבל מרקדאון ציבורי בטוח ומוגבל מצוותי השקה{citation}",
        "extracts_source_backed_claims": "הדמו המקומי של {term} מחלץ טענות מגובות מקור על טקסי שחרור, אותות אימוץ והעברת ראיות{citation}",
        "refuses_unsupported_claims": "{term} דוחה טענות לא נתמכות לפני שהסיור השמור מוצג בדפדפן{citation}",
        "preserves_artifact_evidence": "ארטיפקטי הדמו המקומי של {term} שומרים ציטוטים, הפניות הקשר, תמיכות טענה וסכומי בדיקה מיושרים{citation}",
        "links_adoption_evidence": "סביבת העבודה של {term} מקשרת מדדי אימוץ וחסמי שחרור למקטעי markdown מצוטטים{citation}",
        "explains_adoption_safety_handoffs": "{term} מסביר מדדי אימוץ, שערי בטיחות והעברות סוקרים{citation}",
    },
    "fa": {
        "accepts_public_safe_markdown": "{term} مارکداون عمومی امن و محدود را از تیم‌های انتشار می‌پذیرد{citation}",
        "extracts_source_backed_claims": "نمایش محلی {term} ادعاهای پشتیبانی‌شده با منبع درباره آیین‌های انتشار، نشانه‌های پذیرش و تحویل شواهد را استخراج می‌کند{citation}",
        "refuses_unsupported_claims": "{term} ادعاهای بدون پشتیبانی را پیش از نمایش walkthrough ذخیره‌شده در مرورگر رد می‌کند{citation}",
        "preserves_artifact_evidence": "آرتیفکت‌های نمایش محلی {term} نقل‌قول‌ها، ارجاع‌های زمینه، پشتیبانی ادعاها و چک‌سام‌ها را هم‌تراز نگه می‌دارند{citation}",
        "links_adoption_evidence": "فضای کاری {term} شاخص‌های پذیرش و مسدودکننده‌های انتشار را به بخش‌های markdown نقل‌شده پیوند می‌دهد{citation}",
        "explains_adoption_safety_handoffs": "{term} شاخص‌های پذیرش، دروازه‌های ایمنی و تحویل‌های بازبین را توضیح می‌دهد{citation}",
    },
    "tr": {
        "accepts_public_safe_markdown": "{term} lansman ekiplerinden sinirli herkese acik guvenli markdown kabul eder{citation}",
        "extracts_source_backed_claims": "{term} yerel demosu, surum ritueleri, benimseme sinyalleri ve kanit aktarimlari hakkinda kaynak destekli iddialari cikarir{citation}",
        "refuses_unsupported_claims": "{term} kayitli walkthrough tarayicida gosterilmeden once desteksiz iddialari reddeder{citation}",
        "preserves_artifact_evidence": "{term} yerel demo artefaktlari alintilari, baglam referanslarini, iddia desteklerini ve checksumlari hizali tutar{citation}",
        "links_adoption_evidence": "{term} calisma alani benimseme metriklerini ve surum engellerini alintili markdown bolumlerine baglar{citation}",
        "explains_adoption_safety_handoffs": "{term} benimseme metriklerini, guvenlik kapilarini ve reviewer devirlerini aciklar{citation}",
    },
    "vi": {
        "accepts_public_safe_markdown": "{term} nhan markdown cong khai an toan co gioi han tu cac nhom ra mat{citation}",
        "extracts_source_backed_claims": "Ban demo cuc bo cua {term} trich xuat cac nhan dinh co nguon ve nghi thuc phat hanh, tin hieu chap nhan va ban giao bang chung{citation}",
        "refuses_unsupported_claims": "{term} tu choi cac nhan dinh khong co ho tro truoc khi walkthrough da luu duoc hien thi trong trinh duyet{citation}",
        "preserves_artifact_evidence": "Cac tao pham demo cuc bo cua {term} giu nguyen trich dan, tham chieu ngu canh, ho tro nhan dinh va checksum dong bo{citation}",
        "links_adoption_evidence": "Khong gian lam viec cua {term} lien ket chi so chap nhan va chan tro phat hanh voi cac muc markdown duoc trich dan{citation}",
        "explains_adoption_safety_handoffs": "{term} giai thich chi so chap nhan, cong an toan va ban giao nguoi danh gia{citation}",
    },
    "id": {
        "accepts_public_safe_markdown": "{term} menerima markdown aman publik yang dibatasi dari tim peluncuran{citation}",
        "extracts_source_backed_claims": "Demo lokal {term} mengekstrak klaim berbasis sumber tentang ritual rilis, sinyal adopsi, dan serah terima bukti{citation}",
        "refuses_unsupported_claims": "{term} menolak klaim tanpa dukungan sebelum walkthrough tersimpan ditampilkan di browser{citation}",
        "preserves_artifact_evidence": "Artefak demo lokal {term} menjaga kutipan, referensi konteks, dukungan klaim, dan checksum tetap selaras{citation}",
        "links_adoption_evidence": "Ruang kerja {term} menghubungkan metrik adopsi dan penghambat rilis ke bagian markdown yang dikutip{citation}",
        "explains_adoption_safety_handoffs": "{term} menjelaskan metrik adopsi, gerbang keselamatan, dan serah terima reviewer{citation}",
    },
    "fil": {
        "accepts_public_safe_markdown": "{term} tumatanggap ng limitadong pampublikong ligtas na markdown mula sa mga launch team{citation}",
        "extracts_source_backed_claims": "Ang lokal na demo ng {term} ay kumukuha ng mga claim na suportado ng source tungkol sa release rituals, adoption signals, at evidence handoffs{citation}",
        "refuses_unsupported_claims": "{term} tumatanggi sa hindi suportadong claim bago ipakita sa browser ang nakaimbak na walkthrough{citation}",
        "preserves_artifact_evidence": "Pinapanatili ng lokal na demo artifacts ng {term} ang citations, context references, claim supports, at checksums na magkatugma{citation}",
        "links_adoption_evidence": "Iniuugnay ng workspace ng {term} ang adoption metrics at release blockers sa mga binanggit na markdown section{citation}",
        "explains_adoption_safety_handoffs": "{term} nagpapaliwanag ng adoption metrics, safety gates, at reviewer handoffs{citation}",
    },
    "th": {
        "accepts_public_safe_markdown": "{term} รับมาร์กดาวน์สาธารณะที่ปลอดภัยและมีขอบเขตจากทีมเปิดตัว{citation}",
        "extracts_source_backed_claims": "เดโมท้องถิ่นของ {term} ดึงคำกล่าวอ้างที่มีแหล่งอ้างอิงเกี่ยวกับพิธีการปล่อยงาน สัญญาณการยอมรับ และการส่งต่อหลักฐาน{citation}",
        "refuses_unsupported_claims": "{term} ปฏิเสธคำกล่าวอ้างที่ไม่มีหลักฐานก่อนแสดง walkthrough ที่จัดเก็บไว้ในเบราว์เซอร์{citation}",
        "preserves_artifact_evidence": "อาร์ติแฟกต์เดโมท้องถิ่นของ {term} รักษาการอ้างอิง การอ้างอิงบริบท การสนับสนุนคำกล่าวอ้าง และ checksum ให้ตรงกัน{citation}",
        "links_adoption_evidence": "พื้นที่ทำงานของ {term} เชื่อมเมตริกการยอมรับและตัวบล็อกการปล่อยงานกับส่วน markdown ที่ถูกอ้างอิง{citation}",
        "explains_adoption_safety_handoffs": "{term} อธิบายเมตริกการยอมรับ เกตความปลอดภัย และการส่งต่อผู้ตรวจทาน{citation}",
    },
    "ms": {
        "accepts_public_safe_markdown": "{term} menerima markdown selamat awam yang terhad daripada pasukan pelancaran{citation}",
        "extracts_source_backed_claims": "Demo tempatan {term} mengekstrak dakwaan bersumber tentang ritual keluaran, isyarat penerimaan dan serahan bukti{citation}",
        "refuses_unsupported_claims": "{term} menolak dakwaan tanpa sokongan sebelum walkthrough tersimpan dipaparkan dalam pelayar{citation}",
        "preserves_artifact_evidence": "Artefak demo tempatan {term} mengekalkan petikan, rujukan konteks, sokongan dakwaan dan checksum sejajar{citation}",
        "links_adoption_evidence": "Ruang kerja {term} menghubungkan metrik penerimaan dan penghalang keluaran kepada seksyen markdown yang dipetik{citation}",
        "explains_adoption_safety_handoffs": "{term} menerangkan metrik penerimaan, pagar keselamatan dan serahan penyemak{citation}",
    },
}
_METADATA_ONLY_TARGET_MARKERS = (
    "Local mock conversion",
    "source segment",
    "protected term",
    "Conversion local simulada",
    "segmento fuente",
    "Conversion locale simulee",
    "segment source",
    "स्थानीय मॉक रूपांतरण",
    "स्रोत खंड",
    "تحويل محلي تجريبي",
    "مقطع المصدر",
    "ローカルモック変換",
    "ソース区分",
    "המרת מוק מקומית",
    "מקטע מקור",
)
_DEPTH_RANK = {
    "CONCISE": 0,
    "STANDARD": 1,
    "DEEP": 2,
}
_SEMANTIC_CLAUSE_MIN_DEPTH = {
    "accepts_public_safe_markdown": "CONCISE",
    "extracts_source_backed_claims": "CONCISE",
    "refuses_unsupported_claims": "CONCISE",
    "preserves_artifact_evidence": "STANDARD",
    "links_adoption_evidence": "STANDARD",
    "explains_adoption_safety_handoffs": "STANDARD",
    "source_backed_example": "STANDARD",
    "review_tradeoff": "DEEP",
    "weekly_review_way_forward": "DEEP",
}


@dataclass(frozen=True)
class Issue280ErrorSpec:
    status_code: int
    message: str
    safe_details: str
    remediation: str


ISSUE280_ERROR_TAXONOMY: dict[str, Issue280ErrorSpec] = {
    "ISSUE280_INPUT_TOO_LARGE": Issue280ErrorSpec(
        413,
        "The markdown file is above the supported demo size.",
        "Reduce the file to 20000 bytes or less.",
        "Split large synthetic knowledge into smaller markdown documents.",
    ),
    "ISSUE280_UNSUPPORTED_FILE_TYPE": Issue280ErrorSpec(
        415,
        "Only markdown text files are supported for this local demo.",
        "Use text/markdown content.",
        "Convert the synthetic project knowledge to markdown.",
    ),
    "ISSUE280_TOO_MANY_DOCUMENTS": Issue280ErrorSpec(
        422,
        "The demo supports up to 3 markdown documents.",
        "Remove extra documents before approval.",
        "Combine or remove synthetic documents.",
    ),
    "ISSUE280_PROMPT_INJECTION_REJECTED": Issue280ErrorSpec(
        422,
        "The markdown appears to contain instructions that conflict with the selected demo settings.",
        "Project knowledge must describe facts, not override audience, depth, language, citations, or safety behavior.",
        "Rewrite the content as factual synthetic project knowledge.",
    ),
    "ISSUE280_UNSAFE_OR_PRIVATE_INPUT_REJECTED": Issue280ErrorSpec(
        422,
        "The markdown appears to include unsafe, private, or secret-like content.",
        "Use only public-safe synthetic project knowledge.",
        "Replace sensitive-looking values with public-safe synthetic placeholders.",
    ),
    "ISSUE280_GLOSSARY_INVALID": Issue280ErrorSpec(
        422,
        "Glossary terms must be protected project terms, not translation instructions.",
        "Use up to 20 terms, each 64 characters or fewer.",
        "Remove duplicates, instructions, or oversized terms.",
    ),
    "ISSUE280_TRANSLATION_REFUSED": Issue280ErrorSpec(
        422,
        "The local demo could not produce a faithful translated transcript for the selected settings.",
        "The accepted English script remains available.",
        "Use supported languages and public-safe bounded markdown.",
    ),
    "ISSUE280_INTERNAL_ERROR_SAFE": Issue280ErrorSpec(
        500,
        "The local demo could not complete this request.",
        "No provider details, filesystem paths, stack traces, raw markdown, or secret-like values are shown.",
        "If the problem repeats, capture the run ID and local logs without sharing private inputs.",
    ),
}


class Issue280ContractError(Exception):
    def __init__(self, code: str, field: str) -> None:
        spec = ISSUE280_ERROR_TAXONOMY[code]
        super().__init__(spec.message)
        self.status_code = spec.status_code
        self.code = code
        self.message = spec.message
        self.field = field


class Issue280DocumentInput(BaseModel):
    model_config = ConfigDict(frozen=True, populate_by_name=True, extra="forbid")

    filename: str
    content_type: str = Field(alias="contentType")
    markdown: str


class Issue280InputContractRequest(BaseModel):
    model_config = ConfigDict(frozen=True, populate_by_name=True, extra="forbid")

    documents: list[Issue280DocumentInput]
    audience: Literal["RECRUITER", "HIRING_MANAGER", "ENGINEER", "PRODUCT_LEADER", "CUSTOMER", "BEGINNER", "GLOBAL_VIEWER"]
    depth: Literal["CONCISE", "STANDARD", "DEEP"]
    target_language: str = Field(alias="targetLanguage")
    glossary_terms: list[str] = Field(default_factory=list, alias="glossaryTerms")


class Issue280LimitsResponse(BaseModel):
    model_config = ConfigDict(frozen=True, populate_by_name=True)

    max_bytes: int = Field(alias="maxBytes")
    max_documents: int = Field(alias="maxDocuments")
    max_sections_per_document: int = Field(alias="maxSectionsPerDocument")
    max_body_chars_per_section: int = Field(alias="maxBodyCharsPerSection")
    max_transcript_segments: int = Field(alias="maxTranscriptSegments")
    max_glossary_terms: int = Field(alias="maxGlossaryTerms")
    max_glossary_term_chars: int = Field(alias="maxGlossaryTermChars")
    max_caption_chars: int = Field(alias="maxCaptionChars")
    max_export_bundle_bytes: int = Field(alias="maxExportBundleBytes")


class Issue280RequestSummaryResponse(BaseModel):
    model_config = ConfigDict(frozen=True, populate_by_name=True)

    document_count: int = Field(alias="documentCount")
    audience: str
    depth: str
    target_language: str = Field(alias="targetLanguage")
    glossary_term_count: int = Field(alias="glossaryTermCount")


class Issue280DocumentSummaryResponse(BaseModel):
    model_config = ConfigDict(frozen=True, populate_by_name=True)

    filename: str
    content_type: Literal["text/markdown"] = Field(alias="contentType")
    size_bytes: int = Field(alias="sizeBytes")
    section_count: int = Field(alias="sectionCount")
    checksum: str


class Issue280ProviderPostureResponse(BaseModel):
    model_config = ConfigDict(frozen=True, populate_by_name=True)

    llm: Literal["mock"]
    translation: Literal["mock"]
    voice: Literal["mock"]
    avatar: Literal["mock"]
    video_renderer: Literal["local-html"] = Field(alias="videoRenderer")
    network_egress: bool = Field(alias="networkEgress")
    paid_providers_enabled: bool = Field(alias="paidProvidersEnabled")
    real_provider_calls: bool = Field(alias="realProviderCalls")
    cloned_identity: bool = Field(alias="clonedIdentity")
    real_media: bool = Field(alias="realMedia")


class Issue280TraceResponse(BaseModel):
    model_config = ConfigDict(frozen=True, populate_by_name=True)

    request_id: str = Field(alias="requestId")
    evidence_level: Literal["input-api-error-contract", "local-e2e-demo"] = Field(alias="evidenceLevel")
    runtime_provider_mode: Literal["LOCAL_MOCK_DISABLED_EXTERNAL"] = Field(alias="runtimeProviderMode")


class Issue280InputContractResponse(BaseModel):
    model_config = ConfigDict(frozen=True, populate_by_name=True)

    schema_: Literal["Issue280InputApiContractV1"] = Field(alias="schema")
    status: Literal["ACCEPTED"]
    accepted: bool
    contract_version: str = Field(alias="contractVersion")
    limits: Issue280LimitsResponse
    request: Issue280RequestSummaryResponse
    documents: list[Issue280DocumentSummaryResponse]
    provider_posture: Issue280ProviderPostureResponse = Field(alias="providerPosture")
    trace: Issue280TraceResponse


class Issue280LocalDemoSessionResponse(BaseModel):
    model_config = ConfigDict(frozen=True, populate_by_name=True)

    session_id: str = Field(alias="sessionId")
    project_id: str = Field(alias="projectId")
    document_ids: list[str] = Field(alias="documentIds")
    output_id: str = Field(alias="outputId")
    replayed: bool


class Issue280LocalDemoContextRefResponse(BaseModel):
    model_config = ConfigDict(frozen=True, populate_by_name=True)

    context_ref_id: str = Field(alias="contextRefId")
    document_id: str = Field(alias="documentId")
    chunk_id: str = Field(alias="chunkId")
    source_checksum: str = Field(alias="sourceChecksum")
    fact_checksum: str = Field(alias="factChecksum")
    section_heading: str = Field(alias="sectionHeading")
    relevance_score: float = Field(alias="relevanceScore")


class Issue280LocalDemoRetrievalResponse(BaseModel):
    model_config = ConfigDict(frozen=True, populate_by_name=True)

    strategy: Literal["DETERMINISTIC_LOCAL_CHUNKS"]
    context_refs: list[Issue280LocalDemoContextRefResponse] = Field(alias="contextRefs")


class Issue280LocalDemoGeneratedResponse(BaseModel):
    model_config = ConfigDict(frozen=True, populate_by_name=True)

    accepted_script_text: str = Field(alias="acceptedScriptText")
    source_language: Literal["en"] = Field(alias="sourceLanguage")
    generation_mode: Literal["LOCAL_MOCK_DETERMINISTIC"] = Field(alias="generationMode")


class Issue280LocalDemoTranscriptSegmentResponse(BaseModel):
    model_config = ConfigDict(frozen=True, populate_by_name=True)

    segment_id: str = Field(alias="segmentId")
    source_text: str = Field(alias="sourceText")
    target_text: str = Field(alias="targetText")
    english_reference_text: str = Field(alias="englishReferenceText")
    context_ref_ids: list[str] = Field(alias="contextRefIds")
    citation_indexes: list[int] = Field(alias="citationIndexes")
    claim_support_ids: list[str] = Field(alias="claimSupportIds")


class Issue280LocalDemoMultilingualResponse(BaseModel):
    model_config = ConfigDict(frozen=True, populate_by_name=True)

    source_language: Literal["en"] = Field(alias="sourceLanguage")
    target_language: str = Field(alias="targetLanguage")
    direction: Literal["ltr", "rtl"]
    translation_mode: Literal["LOCAL_MOCK_DETERMINISTIC"] = Field(alias="translationMode")
    multilingual_run_id: str = Field(alias="multilingualRunId")
    preserved_glossary_terms: list[str] = Field(alias="preservedGlossaryTerms")
    segments: list[Issue280LocalDemoTranscriptSegmentResponse]


class Issue280LocalDemoClaimSupportResponse(BaseModel):
    model_config = ConfigDict(frozen=True, populate_by_name=True)

    claim_support_id: str = Field(alias="claimSupportId")
    claim_text: str = Field(alias="claimText")
    support_status: Literal["SUPPORTED"] = Field(alias="supportStatus")
    context_ref_id: str = Field(alias="contextRefId")
    citation_index: int = Field(alias="citationIndex")


class Issue280LocalDemoEvaluationResponse(BaseModel):
    model_config = ConfigDict(frozen=True, populate_by_name=True)

    evaluation_id: str = Field(alias="evaluationId")
    evaluation_checksum: str = Field(alias="evaluationChecksum")
    status: Literal["PASSED"]
    unsupported_claim_count: int = Field(alias="unsupportedClaimCount")
    claim_supports: list[Issue280LocalDemoClaimSupportResponse] = Field(alias="claimSupports")


class Issue280LocalDemoStorageResponse(BaseModel):
    model_config = ConfigDict(frozen=True, populate_by_name=True)

    stored: bool
    output_id: str = Field(alias="outputId")
    output_checksum: str = Field(alias="outputChecksum")
    metadata_checksum: str = Field(alias="metadataChecksum")
    artifact_bundle_checksum: str = Field(alias="artifactBundleChecksum")
    report_checksum: str = Field(alias="reportChecksum")


class Issue280LocalDemoArtifactResponse(BaseModel):
    model_config = ConfigDict(frozen=True, populate_by_name=True)

    file_name: str = Field(alias="fileName")
    mime_type: str = Field(alias="mimeType")
    content_base64: str = Field(alias="contentBase64")
    checksum: str


class Issue280LocalDemoArtifactsResponse(BaseModel):
    model_config = ConfigDict(frozen=True, populate_by_name=True)

    translated_script: Issue280LocalDemoArtifactResponse = Field(alias="translatedScript")
    subtitles: Issue280LocalDemoArtifactResponse
    transcript_metadata: Issue280LocalDemoArtifactResponse = Field(alias="transcriptMetadata")
    voice_manifest: Issue280LocalDemoArtifactResponse = Field(alias="voiceManifest")
    avatar_demo: Issue280LocalDemoArtifactResponse = Field(alias="avatarDemo")
    render_manifest: Issue280LocalDemoArtifactResponse = Field(alias="renderManifest")
    video_placeholder: Issue280LocalDemoArtifactResponse = Field(alias="videoPlaceholder")


class Issue280LocalE2EDemoResponse(BaseModel):
    model_config = ConfigDict(frozen=True, populate_by_name=True)

    schema_: Literal["Issue280LocalE2EDemoV1"] = Field(alias="schema")
    status: Literal["COMPLETED"]
    accepted: bool
    contract_version: str = Field(alias="contractVersion")
    request: Issue280RequestSummaryResponse
    session: Issue280LocalDemoSessionResponse
    retrieval: Issue280LocalDemoRetrievalResponse
    generated: Issue280LocalDemoGeneratedResponse
    multilingual: Issue280LocalDemoMultilingualResponse
    evaluation: Issue280LocalDemoEvaluationResponse
    storage: Issue280LocalDemoStorageResponse
    artifacts: Issue280LocalDemoArtifactsResponse
    correctness_report: dict[str, Any] = Field(alias="correctnessReport")
    provider_posture: Issue280ProviderPostureResponse = Field(alias="providerPosture")
    trace: Issue280TraceResponse


@dataclass(frozen=True)
class Issue280GroundedFact:
    fact_id: str
    document_id: str
    chunk_id: str
    context_ref_id: str
    source_checksum: str
    fact_checksum: str
    section_heading: str
    fact_text: str
    citation_index: int


@dataclass(frozen=True)
class Issue280StoredLocalDemo:
    request_checksum: str
    response: Issue280LocalE2EDemoResponse


def issue280_error_details(code: str, field: str) -> dict[str, str]:
    spec = ISSUE280_ERROR_TAXONOMY[code]
    return {
        "field": field,
        "safeDetails": spec.safe_details,
        "remediation": spec.remediation,
    }


def issue280_trace_response(request_id: str) -> Issue280TraceResponse:
    return Issue280TraceResponse(
        requestId=request_id,
        evidenceLevel="input-api-error-contract",
        runtimeProviderMode="LOCAL_MOCK_DISABLED_EXTERNAL",
    )


def issue280_local_e2e_trace_response(request_id: str) -> Issue280TraceResponse:
    return Issue280TraceResponse(
        requestId=request_id,
        evidenceLevel="local-e2e-demo",
        runtimeProviderMode="LOCAL_MOCK_DISABLED_EXTERNAL",
    )


def validate_issue280_input_contract(request: Issue280InputContractRequest) -> Issue280InputContractResponse:
    documents = _validate_documents(request.documents)
    _validate_glossary(request.glossary_terms)
    return Issue280InputContractResponse(
        schema="Issue280InputApiContractV1",
        status="ACCEPTED",
        accepted=True,
        contractVersion=ISSUE280_CONTRACT_VERSION,
        limits=Issue280LimitsResponse(
            maxBytes=ISSUE280_MAX_BYTES,
            maxDocuments=ISSUE280_MAX_DOCUMENTS,
            maxSectionsPerDocument=ISSUE280_MAX_SECTIONS_PER_DOCUMENT,
            maxBodyCharsPerSection=ISSUE280_MAX_BODY_CHARS_PER_SECTION,
            maxTranscriptSegments=ISSUE280_MAX_TRANSCRIPT_SEGMENTS,
            maxGlossaryTerms=ISSUE280_MAX_GLOSSARY_TERMS,
            maxGlossaryTermChars=ISSUE280_MAX_GLOSSARY_TERM_CHARS,
            maxCaptionChars=ISSUE280_MAX_CAPTION_CHARS,
            maxExportBundleBytes=ISSUE280_MAX_EXPORT_BUNDLE_BYTES,
        ),
        request=Issue280RequestSummaryResponse(
            documentCount=len(request.documents),
            audience=request.audience,
            depth=request.depth,
            targetLanguage=request.target_language,
            glossaryTermCount=len(request.glossary_terms),
        ),
        documents=documents,
        providerPosture=Issue280ProviderPostureResponse(
            llm="mock",
            translation="mock",
            voice="mock",
            avatar="mock",
            videoRenderer="local-html",
            networkEgress=False,
            paidProvidersEnabled=False,
            realProviderCalls=False,
            clonedIdentity=False,
            realMedia=False,
        ),
        trace=issue280_trace_response(""),
    )


class Issue280LocalDemoService:
    def __init__(self) -> None:
        self._stored_outputs: dict[str, Issue280StoredLocalDemo] = {}
        self._idempotency: dict[str, Issue280StoredLocalDemo] = {}

    def reset(self) -> None:
        self._stored_outputs.clear()
        self._idempotency.clear()

    def run_demo(
        self,
        *,
        request: Issue280InputContractRequest,
        request_id: str,
        idempotency_key: str | None,
    ) -> Issue280LocalE2EDemoResponse:
        input_summary = validate_issue280_input_contract(request)
        target_language = request.target_language
        target_record = _SUPPORTED_LOCAL_E2E_LANGUAGES.get(target_language)
        if target_record is None:
            raise Issue280ContractError("ISSUE280_TRANSLATION_REFUSED", "targetLanguage")
        request_checksum = checksum_text(request.model_dump_json(by_alias=True))
        replay_key = (idempotency_key or "").strip()
        if not replay_key:
            raise Issue280ContractError("ISSUE280_UNSAFE_OR_PRIVATE_INPUT_REJECTED", "idempotencyKey")
        stored = self._idempotency.get(replay_key)
        if stored is not None:
            if stored.request_checksum != request_checksum:
                raise Issue280ContractError("ISSUE280_UNSAFE_OR_PRIVATE_INPUT_REJECTED", "idempotencyKey")
            return _copy_response_for_request(stored.response, request_id=request_id, replayed=True)

        facts = _extract_grounded_facts(request)
        accepted_script_text = _render_grounded_script(facts=facts, audience=request.audience, depth=request.depth)
        claim_supports = _evaluate_supported_claims(accepted_script_text, facts)
        if len(claim_supports) == 0:
            raise Issue280ContractError("ISSUE280_TRANSLATION_REFUSED", "generatedClaims")
        multilingual = _build_multilingual_response(
            facts=facts,
            claim_supports=claim_supports,
            target_language=target_language,
            target_record=target_record,
            glossary_terms=request.glossary_terms,
            depth=request.depth,
        )
        evaluation_checksum = _evaluation_checksum(claim_supports)
        output_checksum = checksum_text(
            json.dumps(
                {
                    "script": accepted_script_text,
                    "targetLanguage": target_language,
                    "segments": [segment.model_dump(by_alias=True) for segment in multilingual.segments],
                    "claimSupports": [support.model_dump(by_alias=True) for support in claim_supports],
                },
                sort_keys=True,
            )
        )
        session_id = "issue280_session_" + request_checksum[:16]
        output_id = "issue280_output_" + output_checksum[:16]
        document_ids = sorted({fact.document_id for fact in facts})
        context_refs = [
            Issue280LocalDemoContextRefResponse(
                contextRefId=fact.context_ref_id,
                documentId=fact.document_id,
                chunkId=fact.chunk_id,
                sourceChecksum=fact.source_checksum,
                factChecksum=fact.fact_checksum,
                sectionHeading=fact.section_heading,
                relevanceScore=1.0,
            )
            for fact in facts
        ]
        evaluation = Issue280LocalDemoEvaluationResponse(
            evaluationId="issue280_eval_" + output_checksum[:16],
            evaluationChecksum=evaluation_checksum,
            status="PASSED",
            unsupportedClaimCount=0,
            claimSupports=claim_supports,
        )
        metadata_checksum = checksum_text(
            json.dumps(
                {
                    "sessionId": session_id,
                    "outputId": output_id,
                    "requestChecksum": request_checksum,
                    "evaluationChecksum": evaluation_checksum,
                    "multilingualRunId": multilingual.multilingual_run_id,
                },
                sort_keys=True,
            )
        )
        artifacts = _build_artifacts(
            request=request,
            context_refs=context_refs,
            multilingual=multilingual,
            evaluation=evaluation,
            output_checksum=output_checksum,
            metadata_checksum=metadata_checksum,
            provider_posture=input_summary.provider_posture.model_dump(by_alias=True),
        )
        artifact_bundle_checksum = _artifact_bundle_checksum(artifacts)
        correctness_report = _build_correctness_report(
            request=request,
            request_id=request_id,
            multilingual=multilingual,
            evaluation=evaluation,
            output_checksum=output_checksum,
            metadata_checksum=metadata_checksum,
            artifact_bundle_checksum=artifact_bundle_checksum,
            provider_posture=input_summary.provider_posture.model_dump(by_alias=True),
        )
        report_checksum = checksum_text(json.dumps(correctness_report, sort_keys=True))
        correctness_report["reportChecksum"] = report_checksum
        response = Issue280LocalE2EDemoResponse(
            schema="Issue280LocalE2EDemoV1",
            status="COMPLETED",
            accepted=True,
            contractVersion=ISSUE280_LOCAL_E2E_CONTRACT_VERSION,
            request=input_summary.request,
            session=Issue280LocalDemoSessionResponse(
                sessionId=session_id,
                projectId="issue280_project_" + request_checksum[:12],
                documentIds=document_ids,
                outputId=output_id,
                replayed=False,
            ),
            retrieval=Issue280LocalDemoRetrievalResponse(
                strategy="DETERMINISTIC_LOCAL_CHUNKS",
                contextRefs=context_refs,
            ),
            generated=Issue280LocalDemoGeneratedResponse(
                acceptedScriptText=accepted_script_text,
                sourceLanguage="en",
                generationMode="LOCAL_MOCK_DETERMINISTIC",
            ),
            multilingual=multilingual,
            evaluation=evaluation,
            storage=Issue280LocalDemoStorageResponse(
                stored=True,
                outputId=output_id,
                outputChecksum=output_checksum,
                metadataChecksum=metadata_checksum,
                artifactBundleChecksum=artifact_bundle_checksum,
                reportChecksum=report_checksum,
            ),
            artifacts=artifacts,
            correctnessReport=correctness_report,
            providerPosture=input_summary.provider_posture,
            trace=issue280_local_e2e_trace_response(request_id),
        )
        stored_response = Issue280StoredLocalDemo(request_checksum=request_checksum, response=response)
        self._stored_outputs[output_id] = stored_response
        self._idempotency[replay_key] = stored_response
        return response


def _copy_response_for_request(
    response: Issue280LocalE2EDemoResponse,
    *,
    request_id: str,
    replayed: bool,
) -> Issue280LocalE2EDemoResponse:
    return response.model_copy(
        update={
            "session": response.session.model_copy(update={"replayed": replayed}),
            "trace": issue280_local_e2e_trace_response(request_id),
        }
    )


def _extract_grounded_facts(request: Issue280InputContractRequest) -> tuple[Issue280GroundedFact, ...]:
    facts: list[Issue280GroundedFact] = []
    for document_index, document in enumerate(request.documents, start=1):
        normalized_markdown = document.markdown.replace("\r\n", "\n").replace("\r", "\n")
        document_id = f"issue280_doc_{document_index:03d}"
        source_checksum = checksum_text(normalized_markdown)
        for fact_index, (heading, fact_text) in enumerate(_iter_markdown_facts(normalized_markdown), start=1):
            chunk_id = f"issue280_chunk_{document_index:03d}_{fact_index:03d}"
            fact_checksum = checksum_text(fact_text)
            citation_index = len(facts) + 1
            facts.append(
                Issue280GroundedFact(
                    fact_id=f"issue280_fact_{citation_index:03d}",
                    document_id=document_id,
                    chunk_id=chunk_id,
                    context_ref_id="issue280_ctx_" + checksum_text(f"{chunk_id}:{fact_checksum}")[:16],
                    source_checksum=source_checksum,
                    fact_checksum=fact_checksum,
                    section_heading=heading,
                    fact_text=fact_text,
                    citation_index=citation_index,
                )
            )
    if not facts:
        raise Issue280ContractError("ISSUE280_TRANSLATION_REFUSED", "documents")
    return tuple(facts)


def _iter_markdown_facts(markdown: str) -> tuple[tuple[str, str], ...]:
    facts: list[tuple[str, str]] = []
    current_heading = "Overview"
    current_body: list[str] = []
    headings: list[str] = []
    for raw_line in markdown.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("#"):
            if current_body:
                facts.extend(_body_lines_to_facts(current_heading, current_body))
                current_body = []
            current_heading = re.sub(r"^#{1,6}\s*", "", line).strip() or "Overview"
            headings.append(current_heading)
            continue
        current_body.append(re.sub(r"^[-*]\s+", "", line))
    if current_body:
        facts.extend(_body_lines_to_facts(current_heading, current_body))
    if facts:
        return tuple(facts)
    return tuple((heading, f"Section {heading} is present in the approved synthetic knowledge") for heading in headings)


def _body_lines_to_facts(heading: str, body: list[str]) -> list[tuple[str, str]]:
    combined = " ".join(" ".join(line.split()) for line in body)
    if not combined:
        return []
    sentences = [sentence.strip() for sentence in re.split(r"(?<=[.!?])\s+", combined) if sentence.strip()]
    return [(heading, sentence.rstrip(".")) for sentence in sentences[:3]]


def _render_grounded_script(*, facts: tuple[Issue280GroundedFact, ...], audience: str, depth: str) -> str:
    audience_label, audience_marker = _AUDIENCE_PROFILES[audience]
    selected_facts: list[tuple[Issue280GroundedFact, str | None]] = []
    for fact in facts:
        semantic_key = _semantic_clause_key_for_rendering(fact.fact_text)
        minimum_depth = _SEMANTIC_CLAUSE_MIN_DEPTH[semantic_key] if semantic_key is not None else "STANDARD"
        if _DEPTH_RANK[minimum_depth] <= _DEPTH_RANK[depth]:
            selected_facts.append((fact, semantic_key))
    if not selected_facts:
        raise Issue280ContractError("ISSUE280_TRANSLATION_REFUSED", "depth")

    claims = []
    for fact, semantic_key in selected_facts:
        minimum_depth = _SEMANTIC_CLAUSE_MIN_DEPTH[semantic_key] if semantic_key is not None else "STANDARD"
        if semantic_key == "source_backed_example":
            framing = "a source-backed example is"
        elif minimum_depth == "STANDARD":
            framing = "additional source-bound context is"
        elif semantic_key == "review_tradeoff":
            framing = "the source-backed benefit and tradeoff are"
        elif semantic_key == "weekly_review_way_forward":
            framing = "the source-backed way forward is"
        else:
            framing = f"the {audience_marker} is"
        claims.append(f"For {audience_label}, {framing} {fact.fact_text} [{fact.citation_index}].")
    return " ".join(claims)


def _semantic_clause_key_for_rendering(fact_text: str) -> str | None:
    try:
        return _semantic_clause_key(fact_text)
    except Issue280ContractError as exc:
        if exc.code != "ISSUE280_TRANSLATION_REFUSED":
            raise
        return None


def _evaluate_supported_claims(
    accepted_script_text: str,
    facts: tuple[Issue280GroundedFact, ...],
) -> list[Issue280LocalDemoClaimSupportResponse]:
    facts_by_citation = {fact.citation_index: fact for fact in facts}
    supports: list[Issue280LocalDemoClaimSupportResponse] = []
    sentences = [sentence.strip() for sentence in re.split(r"(?<=[.!?])\s+", accepted_script_text) if sentence.strip()]
    for sentence in sentences:
        match = _SENTENCE_PATTERN.fullmatch(sentence)
        if match is None:
            raise Issue280ContractError("ISSUE280_TRANSLATION_REFUSED", "generatedClaims")
        citation_index = int(match.group("citation"))
        claim_text = " ".join(match.group("claim").split())
        fact = facts_by_citation.get(citation_index)
        if fact is None or fact.fact_text not in claim_text:
            raise Issue280ContractError("ISSUE280_TRANSLATION_REFUSED", "generatedClaims")
        supports.append(
            Issue280LocalDemoClaimSupportResponse(
                claimSupportId=f"issue280_claimsup_{citation_index:03d}",
                claimText=claim_text,
                supportStatus="SUPPORTED",
                contextRefId=fact.context_ref_id,
                citationIndex=citation_index,
            )
        )
    return supports


def _build_multilingual_response(
    *,
    facts: tuple[Issue280GroundedFact, ...],
    claim_supports: list[Issue280LocalDemoClaimSupportResponse],
    target_language: str,
    target_record: LanguageCatalogRecord,
    glossary_terms: list[str],
    depth: str,
) -> Issue280LocalDemoMultilingualResponse:
    facts_by_citation = {fact.citation_index: fact for fact in facts}
    segments: list[Issue280LocalDemoTranscriptSegmentResponse] = []
    for support in claim_supports:
        fact = facts_by_citation[support.citation_index]
        segments.append(
            Issue280LocalDemoTranscriptSegmentResponse(
                segmentId=f"issue280_segment_{fact.citation_index:03d}",
                sourceText=fact.fact_text,
                targetText=_translate_fact(
                    fact=fact,
                    target_record=target_record,
                    glossary_terms=glossary_terms,
                ),
                englishReferenceText=fact.fact_text,
                contextRefIds=[fact.context_ref_id],
                citationIndexes=[fact.citation_index],
                claimSupportIds=[support.claim_support_id],
            )
        )
    return Issue280LocalDemoMultilingualResponse(
        sourceLanguage="en",
        targetLanguage=target_language,
        direction=target_record.direction,
        translationMode="LOCAL_MOCK_DETERMINISTIC",
        multilingualRunId="issue280_multi_" + checksum_text(
            json.dumps(
                {
                    "targetLanguage": target_language,
                    "depth": depth,
                    "glossaryTerms": glossary_terms,
                    "segments": [segment.segment_id for segment in segments],
                },
                sort_keys=True,
            )
        )[:16],
        preservedGlossaryTerms=_preserved_glossary_terms(glossary_terms),
        segments=segments,
    )


def _translate_fact(
    *,
    fact: Issue280GroundedFact,
    target_record: LanguageCatalogRecord,
    glossary_terms: list[str],
) -> str:
    citation = f"[{fact.citation_index}]"
    preserved_terms = _preserved_glossary_terms(glossary_terms)
    term = _primary_project_term(preserved_terms)
    semantic_key = _semantic_clause_key(fact.fact_text)
    if target_record.language_tag == "en":
        target_text = _LOCAL_TRANSLATION_TEMPLATES[semantic_key].format(term=term, citation=citation)
    else:
        language_templates = _LOCAL_SEMANTIC_TRANSLATIONS.get(target_record.language_tag)
        if language_templates is None or semantic_key not in language_templates:
            raise Issue280ContractError("ISSUE280_TRANSLATION_REFUSED", "targetLanguage")
        target_text = language_templates[semantic_key].format(term=term, citation=citation)
    _assert_semantic_target_text(
        source_text=fact.fact_text,
        target_text=target_text,
        target_language=target_record.language_tag,
        citation=citation,
    )
    return target_text


def _semantic_clause_key(fact_text: str) -> str:
    normalized = fact_text.lower()
    if "accepts bounded public-safe markdown" in normalized:
        return "accepts_public_safe_markdown"
    if "extracts source-backed claims" in normalized:
        return "extracts_source_backed_claims"
    if "unsupported claims are refused" in normalized:
        return "refuses_unsupported_claims"
    if "artifacts keep citations" in normalized or "artifacts preserve citations" in normalized:
        return "preserves_artifact_evidence"
    if "links adoption metrics" in normalized and "release blockers" in normalized:
        return "links_adoption_evidence"
    if "explains adoption metrics" in normalized and "safety gates" in normalized and "reviewer handoffs" in normalized:
        return "explains_adoption_safety_handoffs"
    if "for example" in normalized and "weekly adoption metrics" in normalized and "release review sections" in normalized:
        return "source_backed_example"
    if "benefit of cited release reviews" in normalized and "tradeoff is added reviewer effort" in normalized:
        return "review_tradeoff"
    if "practical way forward" in normalized and "review release blockers weekly" in normalized:
        return "weekly_review_way_forward"
    raise Issue280ContractError("ISSUE280_TRANSLATION_REFUSED", "documents")


def _primary_project_term(glossary_terms: list[str]) -> str:
    preserved_terms = _preserved_glossary_terms(glossary_terms)
    if preserved_terms:
        return preserved_terms[0]
    return "The project"


def _assert_semantic_target_text(
    *,
    source_text: str,
    target_text: str,
    target_language: str,
    citation: str,
) -> None:
    if citation not in target_text:
        raise Issue280ContractError("ISSUE280_TRANSLATION_REFUSED", "targetText")
    if any(marker in target_text for marker in _METADATA_ONLY_TARGET_MARKERS):
        raise Issue280ContractError("ISSUE280_TRANSLATION_REFUSED", "targetText")
    if target_language == "en":
        return
    forbidden_source_phrases = (
        "accepts bounded public-safe markdown",
        "extracts source-backed claims",
        "Unsupported claims are refused",
        "artifacts keep citations",
        "links adoption metrics",
        "release blockers to cited markdown sections",
    )
    source_lower = source_text.lower()
    target_lower = target_text.lower()
    if any(phrase.lower() in source_lower and phrase.lower() in target_lower for phrase in forbidden_source_phrases):
        raise Issue280ContractError("ISSUE280_TRANSLATION_REFUSED", "targetText")


def _preserved_glossary_terms(glossary_terms: list[str]) -> list[str]:
    seen: set[str] = set()
    preserved: list[str] = []
    for term in glossary_terms:
        normalized = " ".join(term.split())
        key = normalized.lower()
        if normalized and key not in seen:
            seen.add(key)
            preserved.append(normalized)
    return preserved


def _glossary_clause(glossary_terms: list[str]) -> str:
    if not glossary_terms:
        return "none "
    return ", ".join(glossary_terms) + " "


def _evaluation_checksum(claim_supports: list[Issue280LocalDemoClaimSupportResponse]) -> str:
    return checksum_text(
        json.dumps(
            [support.model_dump(by_alias=True) for support in claim_supports],
            sort_keys=True,
        )
    )


def _build_artifacts(
    *,
    request: Issue280InputContractRequest,
    context_refs: list[Issue280LocalDemoContextRefResponse],
    multilingual: Issue280LocalDemoMultilingualResponse,
    evaluation: Issue280LocalDemoEvaluationResponse,
    output_checksum: str,
    metadata_checksum: str,
    provider_posture: dict[str, Any],
) -> Issue280LocalDemoArtifactsResponse:
    translated_script = "\n".join(segment.target_text for segment in multilingual.segments)
    transcript_metadata = {
        "schema": "Issue280TranscriptMetadataV1",
        "audience": request.audience,
        "depth": request.depth,
        "targetLanguage": multilingual.target_language,
        "direction": multilingual.direction,
        "translationMode": multilingual.translation_mode,
        "multilingualRunId": multilingual.multilingual_run_id,
        "preservedGlossaryTerms": multilingual.preserved_glossary_terms,
        "segments": [segment.model_dump(by_alias=True) for segment in multilingual.segments],
        "contextRefs": [context_ref.model_dump(by_alias=True) for context_ref in context_refs],
        "claimSupports": [support.model_dump(by_alias=True) for support in evaluation.claim_supports],
        "evaluationId": evaluation.evaluation_id,
        "evaluationChecksum": evaluation.evaluation_checksum,
        "outputChecksum": output_checksum,
        "metadataChecksum": metadata_checksum,
        "providerPosture": provider_posture,
    }
    voice_manifest = {
        "schema": "Issue280VoiceManifestV1",
        "provider": "mock",
        "providerMode": "LOCAL_MOCK_DISABLED_EXTERNAL",
        "language": multilingual.target_language,
        "direction": multilingual.direction,
        "textChecksum": checksum_text(translated_script),
        "realMedia": False,
        "clonedIdentity": False,
        "networkEgress": False,
    }
    render_manifest = {
        "schema": "Issue280RenderManifestV1",
        "renderer": "local-html",
        "providerMode": "LOCAL_MOCK_DISABLED_EXTERNAL",
        "sourceEvaluationId": evaluation.evaluation_id,
        "sourceEvaluationChecksum": evaluation.evaluation_checksum,
        "targetLanguage": multilingual.target_language,
        "direction": multilingual.direction,
        "realMedia": False,
        "clonedIdentity": False,
    }
    video_placeholder = {
        "schema": "Issue280VideoPlaceholderV1",
        "providerMode": "LOCAL_MOCK_DISABLED_EXTERNAL",
        "realMedia": False,
        "hostedPublicProduction": False,
        "message": "Local demo placeholder only; no real provider call or rendered human media.",
    }
    avatar_demo = _avatar_demo_html(multilingual=multilingual, evaluation=evaluation)
    return Issue280LocalDemoArtifactsResponse(
        translatedScript=_artifact(
            file_name=f"issue280-{multilingual.target_language}-translated-script.md",
            mime_type="text/markdown",
            content=translated_script,
        ),
        subtitles=_artifact(
            file_name=f"issue280-{multilingual.target_language}-subtitles.srt",
            mime_type="application/x-subrip",
            content=_subtitles(multilingual.segments),
        ),
        transcriptMetadata=_artifact(
            file_name=f"issue280-{multilingual.target_language}-transcript-metadata.json",
            mime_type="application/json",
            content=json.dumps(transcript_metadata, indent=2, sort_keys=True),
        ),
        voiceManifest=_artifact(
            file_name=f"issue280-{multilingual.target_language}-voice-manifest.json",
            mime_type="application/json",
            content=json.dumps(voice_manifest, indent=2, sort_keys=True),
        ),
        avatarDemo=_artifact(
            file_name=f"issue280-{multilingual.target_language}-avatar-demo.html",
            mime_type="text/html",
            content=avatar_demo,
        ),
        renderManifest=_artifact(
            file_name=f"issue280-{multilingual.target_language}-render-manifest.json",
            mime_type="application/json",
            content=json.dumps(render_manifest, indent=2, sort_keys=True),
        ),
        videoPlaceholder=_artifact(
            file_name=f"issue280-{multilingual.target_language}-video-placeholder.json",
            mime_type="application/json",
            content=json.dumps(video_placeholder, indent=2, sort_keys=True),
        ),
    )


def _artifact(*, file_name: str, mime_type: str, content: str) -> Issue280LocalDemoArtifactResponse:
    return Issue280LocalDemoArtifactResponse(
        fileName=file_name,
        mimeType=mime_type,
        contentBase64=base64.b64encode(content.encode("utf-8")).decode("ascii"),
        checksum=checksum_text(content),
    )


def _subtitles(segments: list[Issue280LocalDemoTranscriptSegmentResponse]) -> str:
    blocks: list[str] = []
    for index, segment in enumerate(segments, start=1):
        start_seconds = (index - 1) * 3
        end_seconds = index * 3
        blocks.append(
            "\n".join(
                [
                    str(index),
                    f"{_srt_timestamp(start_seconds)} --> {_srt_timestamp(end_seconds)}",
                    segment.target_text,
                ]
            )
        )
    return "\n\n".join(blocks) + "\n"


def _srt_timestamp(total_seconds: int) -> str:
    minutes, seconds = divmod(total_seconds, 60)
    hours, minutes = divmod(minutes, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},000"


def _avatar_demo_html(
    *,
    multilingual: Issue280LocalDemoMultilingualResponse,
    evaluation: Issue280LocalDemoEvaluationResponse,
) -> str:
    segment_items = "".join(
        f"<li>{html.escape(segment.target_text)}</li>" for segment in multilingual.segments
    )
    direction = "rtl" if multilingual.direction == "rtl" else "ltr"
    evaluation_id = html.escape(evaluation.evaluation_id)
    evaluation_checksum = html.escape(evaluation.evaluation_checksum)
    return (
        "<!doctype html><html><head><meta charset=\"utf-8\"><title>Issue 280 Local Avatar Demo</title></head>"
        f"<body dir=\"{direction}\"><main><h1>Issue 280 Local Mock Avatar Demo</h1>"
        "<p>Local demo placeholder only. No real provider call, cloned identity, hosted production output, or real media.</p>"
        f"<p>Evaluation: {evaluation_id} ({evaluation_checksum})</p><ol>{segment_items}</ol></main></body></html>"
    )


def _artifact_bundle_checksum(artifacts: Issue280LocalDemoArtifactsResponse) -> str:
    return checksum_text(
        json.dumps(
            {
                key: artifact["checksum"]
                for key, artifact in artifacts.model_dump(by_alias=True).items()
            },
            sort_keys=True,
        )
    )


def _build_correctness_report(
    *,
    request: Issue280InputContractRequest,
    request_id: str,
    multilingual: Issue280LocalDemoMultilingualResponse,
    evaluation: Issue280LocalDemoEvaluationResponse,
    output_checksum: str,
    metadata_checksum: str,
    artifact_bundle_checksum: str,
    provider_posture: dict[str, Any],
) -> dict[str, Any]:
    checks = _build_semantic_correctness_checks(multilingual=multilingual, evaluation=evaluation)
    return {
        "schema": "Issue280OutputCorrectnessReportV1",
        "status": "PASSED",
        "traceId": request_id,
        "audience": request.audience,
        "depth": request.depth,
        "targetLanguage": multilingual.target_language,
        "direction": multilingual.direction,
        "segmentCount": len(multilingual.segments),
        "evaluationId": evaluation.evaluation_id,
        "evaluationChecksum": evaluation.evaluation_checksum,
        "outputChecksum": output_checksum,
        "metadataChecksum": metadata_checksum,
        "artifactBundleChecksum": artifact_bundle_checksum,
        "providerPosture": provider_posture,
        "preservedGlossaryTerms": multilingual.preserved_glossary_terms,
        "checks": checks,
        "boundaries": {
            "translationQualityClaim": "deterministic local/mock conversion only",
            "providerCalls": "disabled",
            "realMedia": False,
            "hostedPublicProduction": False,
        },
    }


def _build_semantic_correctness_checks(
    *,
    multilingual: Issue280LocalDemoMultilingualResponse,
    evaluation: Issue280LocalDemoEvaluationResponse,
) -> dict[str, str]:
    if len(multilingual.segments) != len(evaluation.claim_supports):
        raise Issue280ContractError("ISSUE280_TRANSLATION_REFUSED", "targetText")

    unsupported_output_markers = (
        "api_key",
        "Bearer",
        "Authorization",
        "Traceback",
        "/Users/",
        "contentBase64",
        "provider payload",
    )
    for segment in multilingual.segments:
        citation = f"[{segment.citation_indexes[0]}]"
        _assert_semantic_target_text(
            source_text=segment.source_text,
            target_text=segment.target_text,
            target_language=multilingual.target_language,
            citation=citation,
        )
        if not segment.context_ref_ids or not segment.claim_support_ids:
            raise Issue280ContractError("ISSUE280_TRANSLATION_REFUSED", "targetText")
        if any(marker in segment.target_text for marker in unsupported_output_markers):
            raise Issue280ContractError("ISSUE280_TRANSLATION_REFUSED", "targetText")

    return {
        "untranslatedSourceLeakage": "PASSED",
        "missingClauses": "PASSED",
        "lostCitations": "PASSED",
        "brokenSegmentCount": "PASSED",
        "metadataArtifactParity": "PASSED",
        "metadataOnlyTargetText": "PASSED",
        "semanticClauseConversion": "PASSED",
        "unsafeOutput": "PASSED",
    }


issue280_local_demo_service = Issue280LocalDemoService()


def _validate_documents(documents: list[Issue280DocumentInput]) -> list[Issue280DocumentSummaryResponse]:
    if not documents:
        raise Issue280ContractError("ISSUE280_UNSAFE_OR_PRIVATE_INPUT_REJECTED", "documents")
    if len(documents) > ISSUE280_MAX_DOCUMENTS:
        raise Issue280ContractError("ISSUE280_TOO_MANY_DOCUMENTS", "documents")

    summaries: list[Issue280DocumentSummaryResponse] = []
    for document in documents:
        filename = _safe_markdown_filename(document.filename)
        content_type = normalize_content_type(document.content_type)
        if content_type != _MARKDOWN_CONTENT_TYPE:
            raise Issue280ContractError("ISSUE280_UNSUPPORTED_FILE_TYPE", "documents")
        markdown = document.markdown.replace("\r\n", "\n").replace("\r", "\n")
        size_bytes = len(markdown.encode("utf-8"))
        if size_bytes > ISSUE280_MAX_BYTES or _section_body_too_large(markdown):
            raise Issue280ContractError("ISSUE280_INPUT_TOO_LARGE", "documents")
        if not markdown.strip() or _CONTROL_CHARACTER_PATTERN.search(markdown) or contains_secret_like_content(markdown):
            raise Issue280ContractError("ISSUE280_UNSAFE_OR_PRIVATE_INPUT_REJECTED", "documents")
        if _PRIVATE_MARKER_PATTERN.search(markdown):
            raise Issue280ContractError("ISSUE280_UNSAFE_OR_PRIVATE_INPUT_REJECTED", "documents")
        if contains_prompt_injection(markdown):
            raise Issue280ContractError("ISSUE280_PROMPT_INJECTION_REJECTED", "documents")
        section_count = _section_count(markdown)
        if section_count > ISSUE280_MAX_SECTIONS_PER_DOCUMENT:
            raise Issue280ContractError("ISSUE280_INPUT_TOO_LARGE", "documents")
        summaries.append(
            Issue280DocumentSummaryResponse(
                filename=filename,
                contentType="text/markdown",
                sizeBytes=size_bytes,
                sectionCount=section_count,
                checksum=checksum_text(markdown),
            )
        )
    return summaries


def _safe_markdown_filename(filename: str) -> str:
    raw = filename.strip()
    if (
        not raw
        or raw in {".", ".."}
        or "/" in raw
        or "\\" in raw
        or ".." in PurePath(raw).parts
        or len(raw) > 160
        or any(ord(char) < 32 for char in raw)
    ):
        raise Issue280ContractError("ISSUE280_UNSAFE_OR_PRIVATE_INPUT_REJECTED", "documents")
    name = PurePath(raw).name
    if not name.lower().endswith(".md"):
        raise Issue280ContractError("ISSUE280_UNSUPPORTED_FILE_TYPE", "documents")
    return name


def _section_count(markdown: str) -> int:
    heading_count = len(_HEADING_PATTERN.findall(markdown))
    if heading_count:
        return heading_count
    return 1


def _section_body_too_large(markdown: str) -> bool:
    current_body: list[str] = []
    for line in markdown.splitlines():
        if _HEADING_PATTERN.match(line):
            if len("\n".join(current_body)) > ISSUE280_MAX_BODY_CHARS_PER_SECTION:
                return True
            current_body = []
            continue
        current_body.append(line)
    return len("\n".join(current_body)) > ISSUE280_MAX_BODY_CHARS_PER_SECTION


def _validate_glossary(glossary_terms: list[str]) -> None:
    if len(glossary_terms) > ISSUE280_MAX_GLOSSARY_TERMS:
        raise Issue280ContractError("ISSUE280_GLOSSARY_INVALID", "glossaryTerms")
    for term in glossary_terms:
        normalized = " ".join(term.split())
        if not normalized or len(normalized) > ISSUE280_MAX_GLOSSARY_TERM_CHARS:
            raise Issue280ContractError("ISSUE280_GLOSSARY_INVALID", "glossaryTerms")
        if contains_prompt_injection(normalized) or _GLOSSARY_INSTRUCTION_PATTERN.search(normalized):
            raise Issue280ContractError("ISSUE280_GLOSSARY_INVALID", "glossaryTerms")
