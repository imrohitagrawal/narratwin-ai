#!/usr/bin/env python3
"""Issue #452 executable Cut 1 governance contract.

C2 intentionally exposes a typed, import-safe RED skeleton. C4 may replace only
the marked implementation region after the C3 freeze binds this exact contract.
No function performs provider calls, media work, credential resolution, or egress.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence


@dataclass(frozen=True, slots=True)
class Finding:
    """A deterministic contract finding."""

    code: str
    path: str
    message: str


NOT_IMPLEMENTED = Finding(
    code="CUT1.NOT_IMPLEMENTED",
    path="$",
    message="Issue #452 C2 RED skeleton; implementation is frozen for C4.",
)


def finding_codes(findings: Sequence[Finding]) -> tuple[str, ...]:
    """Return stable codes for literal test expectations."""

    return tuple(finding.code for finding in findings)


# C4_IMPLEMENTATION_REGION_START
_datetime = __import__("datetime")
_hash = __import__("hashlib")
_math = __import__("math")
_re = __import__("re")
_GOV = Path(__file__).resolve().parents[2] / "docs/governance"
_SCRIPT_SHA = "3b071180d4723784d84f5005644fc5a2aa5ef6b6adb6f7caeba2de76d68be435"
_KNOWLEDGE_SHA = "49b75655ddbbe43145a35215069bce2751de66393b39eb68d69b584d7ecfcc5e"
_FREEZE_SHA = "b9921a468f1383a3525879144992fd9ccb30c3dbf62481dcfc9f6e2d3b8afceb"
_LIVE_SHA = "89199278feabfdcee21fffe4a9ad4d157dd7fc9a11a2529562876cb6ecc74702"
_NAMES = (
    "cut1-blinded-human-evaluation-protocol-v1.json",
    "cut1-all-presenter-acceptance-matrix-v1.json",
    "cut1-provider-bakeoff-contract-v1.json",
)
_OWNER_COMMENT = "https://github.com/imrohitagrawal/narratwin-ai/issues/452#issuecomment-"
_Doc = Mapping[str, Any]
_Findings = tuple[Finding, ...]
_RL, _RID, _SEV, _PID = "raterLabels", "raterId", "adjudicatedSevere", "presenterId"
_OP, _REV = "operationalInvalidRerunCount", "revisedCandidateRetestCount"
_MODEL, _SOURCES = "modelOrEngine", "officialSourceUrls"
_VIEWERS, _RESPONSE_SHA = "totalUniqueViewerCount", "responseSha256"
_SIDE, _CHOICE, _EXPECTED, _PROJECT = "candidateSide", "forcedChoice", "expectedClass", "projectId"
_LIVE_ROWS, _CANDIDATE = "liveRows", "candidate"
_PROVIDER_STATE, _LOCAL_STATE = "providerState", "localState"
_CLIP_SHA, _VIEWER_MANIFEST = "candidateClipSha256", "viewerManifestSha256"
_CALIBRATION = "sharedCalibration"
def _fail(scope: str, code: str, path: str = "$") -> _Findings: return (Finding(f"CUT1.{scope}.{code}", path, code.lower()),)
def _read(path: Path) -> dict[str,Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value,dict):
        raise ValueError
    return value
_PPL = {row[_PID]: row for row in _read(_GOV / _NAMES[1])["presenters"]}
def _sha_json(value: _Doc) -> str:
    return str(_hash.sha256(json.dumps(value,sort_keys=True,separators=(",",":")).encode()).hexdigest())
def _cell(c: _Doc) -> str: return f"{c[_PID]}-en-{c['aspectRatio'].lower()}"
def _time(value: Any) -> Any:
    try:
        if not isinstance(value,str) or _re.fullmatch(r"\d{4}-\d\d-\d\d[Tt]\d\d:\d\d:\d\d(?:\.\d+)?(?:[Zz]|[+-]\d\d:\d\d)",value) is None:
            return None
        parsed = _datetime.datetime.fromisoformat(value[:-1] + "+00:00" if value[-1] in "Zz" else value)
        return parsed if parsed.tzinfo is not None else None
    except (TypeError,ValueError):
        return None
def _valid(x: Any,s: _Doc,root: _Doc) -> bool:
    if "$ref" in s:
        return _valid(x,root["$defs"][s["$ref"].rsplit("/",1)[1]],root)
    if "oneOf" in s and sum(_valid(x,item,root) for item in s["oneOf"]) != 1:
        return False
    kinds = s.get("type")
    kinds = [kinds] if isinstance(kinds,str) else kinds
    checks = {"object": isinstance(x,dict),"array": isinstance(x,list),"string": isinstance(x,str)}
    checks |= {"integer": isinstance(x,int) and not isinstance(x,bool),"number": isinstance(x,(int,float)) and not isinstance(x,bool) and x == x and x not in (float("inf"),float("-inf")),"boolean": isinstance(x,bool),"null": x is None}
    if kinds and not any(checks[kind] for kind in kinds):
        return False
    if "const" in s and x != s["const"] or "enum" in s and x not in s["enum"]:
        return False
    if isinstance(x,dict):
        props = s.get("properties",{})
        return not any(key not in x for key in s.get("required",[])) and not (s.get("additionalProperties") is False and any(key not in props for key in x)) and all(_valid(item,props[key],root) for key,item in x.items() if key in props)
    if isinstance(x,list):
        return len(x) >= s.get("minItems",0) and len(x) <= s.get("maxItems",len(x)) and not (s.get("uniqueItems") and len({_sha_json({"item": item}) for item in x}) != len(x)) and not ("items" in s and any(not _valid(item,s["items"],root) for item in x))
    if isinstance(x,str):
        return len(x) >= s.get("minLength",0) and len(x) <= s.get("maxLength",len(x)) and not ("pattern" in s and _re.search(s["pattern"],x) is None) and not (s.get("format") == "date-time" and _time(x) is None)
    if isinstance(x,(int,float)) and not isinstance(x,bool):
        return x >= s.get("minimum",x) and x <= s.get("maximum",x) and not ("exclusiveMinimum" in s and x <= s["exclusiveMinimum"])
    return True
def _irr(rows: Sequence[_Doc]) -> tuple[float,float | None]:
    ids = sorted({label[_RID] for label in rows[0][_RL]})
    if len(ids) != 2 or any({label[_RID] for label in row[_RL]} != set(ids) for row in rows):
        raise ValueError("inconsistent raters")
    pairs = [[bool(next(label["severe"] for label in row[_RL] if label[_RID] == rid)) for rid in ids] for row in rows]
    agreement = sum(q[0] == q[1] for q in pairs) / len(pairs)
    rates = [sum(q[index] for q in pairs) / len(pairs) for index in (0,1)]
    return agreement,(agreement - chance) / (1 - chance) if (chance := rates[0] * rates[1] + (1 - rates[0]) * (1 - rates[1])) < 1 else None
def _cal_ok(cal: _Doc) -> bool:
    for rater in cal["raters"]:
        rows = [(row[_EXPECTED], next(label["severe"] for label in row[_RL] if label[_RID] == rater[_RID])) for row in cal["rows"]]
        rates = {
            "overallSensitivity": sum(label for name,label in rows if name != "CLEAN") / 30,
            "identitySensitivity": sum(label for name,label in rows if name == "IDENTITY") / 10,
            "limbSensitivity": sum(label for name,label in rows if name == "LIMB") / 10,
            "temporalSensitivity": sum(label for name,label in rows if name == "TEMPORAL") / 10,
            "specificity": sum(not label for name,label in rows if name == "CLEAN") / 30}
        if any(abs(rater[key] - value) > 1e-12 for key,value in rates.items()) or any(rater[key] != 1 for key in ("overallSensitivity","identitySensitivity","limbSensitivity","temporalSensitivity")) or rater["specificity"] < 0.9:
            return False
    return True
def _retest(c: _Doc,manifest: str) -> bool:
    row, artifact = c["retest"], c[_CANDIDATE]["artifactSha256"]
    attempt,kind,prior = row["attemptNumber"],row["attemptKind"],row["priorDisposition"]
    if row["freshViewerManifestSha256"] != manifest:
        return False
    if attempt == 1:
        return bool(kind == "INITIAL" and prior == "NONE" and row[_OP] == row[_REV] == 0 and row["priorAttemptRef"] is row["priorArtifactSha256"] is row["priorViewerManifestSha256"] is None)
    if row["priorAttemptRef"] is None or row["priorViewerManifestSha256"] == row["freshViewerManifestSha256"]:
        return False
    if kind == "OPERATIONAL_INVALID_RERUN":
        return bool(attempt == 2 and prior == "INVALID" and row["priorArtifactSha256"] == artifact and row[_OP] == 1 and row[_REV] == 0)
    return bool(kind == "REVISED_CANDIDATE_RETEST" and prior in {"FAILED_STATISTICAL","INCONCLUSIVE"} and row["priorArtifactSha256"] != artifact and row[_REV] == 1 and (attempt == 2 and row[_OP] == 0 or attempt == 3 and row[_OP] == 1))
def _human(d: _Doc) -> _Findings:
    def bad(code: str) -> _Findings: return _fail("HUMAN", code)
    sample,plan = d.get("cohort"),d.get("protocolBinding")
    if not isinstance(sample, dict) or not isinstance(sample.get(_VIEWERS), int) or isinstance(sample.get(_VIEWERS), bool) or not isinstance(plan, dict) or _time(plan.get("frozenAt")) is None:
        return bad("SCHEMA")
    if d["activation"] != "NONE" or d["authorityEffect"] != "NO_AUTHORITY_EFFECT":
        return bad("AUTHORITY_BINDING")
    if plan.get("protocolSha256") != _hash.sha256((_GOV / _NAMES[0]).read_bytes()).hexdigest() or plan.get("baseCommit") != "97e8173c2ec1323aa9ced23d43059bca2e5a204f" or set(plan["ownerDecisionRefs"]) != {_OWNER_COMMENT + number for number in ("5444058376","5444076231","5444690736")}:
        return bad("AUTHORITY_BINDING")
    if (frozen := _time(plan.get("frozenAt"))) is None or (shown := _time(plan.get("firstExposureAt"))) is None or frozen >= shown or plan.get("randomizationSeed") != 4522026082801:
        return bad("PREREGISTRATION")
    if len(cells := d["cells"]) != 6 or {(c.get(_PID),c.get("language"),c.get("aspectRatio")) for c in cells} != {(p,"en",a) for p in _PPL for a in ("LANDSCAPE","PORTRAIT")}:
        return bad("CELL_SET")
    if len({c[_CANDIDATE]["tenantId"] for c in cells}) != 1 or len({c[_CANDIDATE][_PROJECT] for c in cells}) != 1:
        return bad("AUTHORITY_BINDING")
    cal, qualified = d[_CALIBRATION], {r[_RID] for r in d[_CALIBRATION]["raters"]}
    if len(qualified) != 2:
        return bad("CALIBRATION")
    links: dict[tuple[str,str],str] = {}
    for c in cells:
        cand, person = c[_CANDIDATE], _PPL[c[_PID]]
        if cand.get("assetSha256") != person["assetSha256"]:
            return bad("ASSET_BINDING")
        if cand.get("scriptSha256") != _SCRIPT_SHA or cand.get("knowledgeSha256") != _KNOWLEDGE_SHA:
            return bad("SOURCE_BINDING")
        if len(pairs := c["pairs"]) != 20 or any(len({p[key] if key in p else p["control"][key] for p in pairs}) != 20 for key in ("pairId","excerptId",_CLIP_SHA,"allocationId","controlId","artifactSha256","manifestSha256")):
            return bad("PAIR_ALLOCATION")
        for q in pairs:
            links[(_cell(c),q["pairId"])] = q["excerptId"]
            effective,expiry = _time((ctrl := q["control"])["effectiveAt"]),_time(ctrl["expiresAt"])
            if effective is None or expiry is None or ctrl[_PROJECT] != cand[_PROJECT] or effective > shown or expiry <= shown:
                return bad("CONTROL_CONSENT")
            if abs(q["candidateDurationMs"] - q["controlDurationMs"]) / q["candidateDurationMs"] > 0.05 or abs(q["candidateLufs"] - q["controlLufs"]) > 1:
                return bad("MATCHING")
    if sample[_VIEWERS] != 200 or len(sample["viewers"]) != 200 or len({row["viewerId"] for row in sample["viewers"]}) != 200 or sample["trialsPerViewerTotal"] != 12:
        return bad("COHORT")
    orders,rows,scores = dict[tuple[str,...],int](),list[_Doc](),list[int]()
    for v in sample["viewers"]:
        if len(batch := v["trials"]) != 12 or [row["order"] for row in batch] != list(range(1,13)):
            return bad("SCHEMA")
        seq = tuple(row["cellId"] for row in batch)
        orders[seq] = orders.get(seq,0) + 1
        if any(seq.count(cid) != 2 for cid in {f"{p}-en-{a}" for p in _PPL for a in ("landscape","portrait")}) or any(seq[i].split("-en-")[0] == seq[i - 1].split("-en-")[0] or seq[i].rsplit("-",1)[1] == seq[i - 1].rsplit("-",1)[1] for i in range(1,12)):
            return bad("ORDER_FATIGUE")
        rows.extend(batch)
        scores.append(sum(bool(row["correct"]) for row in batch))
    if len(orders) != 6 or any(count not in {33,34} for count in orders.values()):
        return bad("ORDER_FATIGUE")
    if sample["totalRatingCount"] != len(rows) or len(rows) != 2400:
        return bad("COUNT_PARITY")
    if len({row["responseId"] for row in rows}) != len(rows):
        return bad("RAW_RESPONSE")
    groups: dict[tuple[str,str],list[_Doc]] = {}
    for v in sample["viewers"]:
        seen: set[tuple[str,str]] = set()
        for row in v["trials"]:
            if row["viewerId"] != v["viewerId"]:
                return bad("RAW_RESPONSE")
            key = (row["cellId"],row["pairId"])
            if key not in links or links[key] != row["excerptId"] or key in seen:
                return bad("PAIR_ALLOCATION")
            seen.add(key)
            body = {k: v for k,v in row.items() if k != _RESPONSE_SHA}
            if row[_RESPONSE_SHA] != _sha_json(body) or row["correct"] != (row[_CHOICE] == row[_SIDE]):
                return bad("RAW_RESPONSE")
            groups.setdefault(key,[]).append(row)
    if any(len(group) != 20 for group in groups.values()):
        return bad("PAIR_ALLOCATION")
    if any(sum(row[_SIDE] == "A" for row in group) != 10 for group in groups.values()):
        return bad("RAW_RESPONSE")
    if len(set(ps := [sum(bool(row["correct"]) for row in group) for group in groups.values()])) == 1 or min(ps) == 0 or max(ps) == 20 or len(set(scores)) < 2:
        return bad("MODEL")
    by_cell = {_cell(c): [r for r in rows if r["cellId"] == _cell(c)] for c in cells}
    for c in cells:
        cid,stats = _cell(c),c["analysis"]
        raw = by_cell[cid]
        if stats["powerSeed"] != 4522026082803 or stats["bootstrapSeed"] != 4522026082802:
            return bad("PREREGISTRATION")
        if stats["forcedChoiceCount"] != len(raw) or stats["pairCount"] != len(c["pairs"]) or stats["minimumRatingsPerPair"] != min(counts := [len(group) for key,group in groups.items() if key[0] == cid]) or stats["maximumRatingsPerPair"] != max(counts):
            return bad("SAMPLE" if stats["forcedChoiceCount"] != len(raw) else "PAIR_ALLOCATION")
        if stats["correctCount"] == 190 and stats["unsureConfidenceCount"] == 20 or stats["unsureConfidenceCount"] != sum(row["confidence"] == "UNSURE" for row in raw):
            return bad("RAW_RESPONSE")
        if stats["correctCount"] != sum(bool(r["correct"]) for r in raw) or stats["viewerCount"] != 200 or stats["missingCount"] != 0 or stats["viewerTrialManifestSha256"] != sample[_VIEWER_MANIFEST]:
            return bad("COUNT_PARITY")
        if not stats["ciLower"] > 0.4 or not stats["ciUpper"] < 0.6 or not stats["ciLower"] <= stats["pointEstimate"] <= stats["ciUpper"]:
            return bad("EQUIVALENCE")
        if not stats["modelConverged"] or stats["modelSingular"]:
            return bad("MODEL")
        if stats["bootstrapSuccessfulDraws"] < 10000 or stats["bootstrapSuccessRate"] < 0.99 or abs(stats["bootstrapSuccessRate"] - stats["bootstrapSuccessfulDraws"] / stats["bootstrapAttemptedDraws"]) > 1e-12:
            return bad("BOOTSTRAP")
        p,z = stats["powerSimulatedPassCount"] / (n := stats["powerSimulationCount"]),1.959963984540054
        wilson = (p + z*z/(2*n) - z*_math.sqrt(p*(1-p)/n + z*z/(4*n*n))) / (1 + z*z/n)
        if n < 100000 or stats["simulatedPower"] < 0.9 or stats["powerWilsonLower"] < 0.9 or abs(stats["simulatedPower"] - p) > 1e-12 or abs(stats["powerWilsonLower"] - wilson) > stats["powerWilsonTolerance"]:
            return bad("POWER")
        ex,reasons = c["exclusions"],[row["count"] for row in c["exclusions"]["reasonRows"]]
        denom = ex["eligibleCount"] + ex["excludedCount"]
        if ex["eligibleCount"] != sample[_VIEWERS] or ex["excludedCount"] != sum(reasons) or abs(ex["totalRate"] - ex["excludedCount"] / denom) > 1e-12 or abs(ex["maximumSingleReasonRate"] - (max(reasons,default=0) / denom)) > 1e-12 or ex["totalRate"] > 0.1 or ex["maximumSingleReasonRate"] > 0.05:
            return bad("EXCLUSION")
        subgroups_bad = any(row["disposition"] != "PASSED" or row["viewerCount"] != stats["viewerCount"] or any(row[key] != stats[key] for key in ("pointEstimate","ciLower","ciUpper")) for row in c["subgroups"])
        if plan["governedSubgroupIds"] != ["all-eligible"] or {row["subgroupId"] for row in c["subgroups"]} != set(plan["governedSubgroupIds"]) or subgroups_bad:
            return bad("SUBGROUP")
        if len(dims := c["dimensions"]) != 17 or len({row["dimension"] for row in dims}) != 17:
            return bad("DIMENSION_SET")
        for dim in dims:
            dimension_bad = dim["scorableEventCount"] != len(clips := dim["clipRows"]) or dim["failCount"] or dim["uncertainCount"] or dim["passCount"] != len(clips)
            labels = [clip["adjudicatedLabel"] for clip in clips]
            dimension_bad |= len(clips) != 20 or len({clip["clipId"] for clip in clips}) != 20 or {clip["clipSha256"] for clip in clips} != {q[_CLIP_SHA] for q in c["pairs"]}
            dimension_bad |= dim["passCount"] != labels.count("PASS") or dim["failCount"] != labels.count("FAIL") or dim["uncertainCount"] != labels.count("UNCERTAIN")
            if dimension_bad:
                return bad("DIMENSION")
            for clip in clips:
                labs = clip[_RL]
                if len({label[_RID] for label in labs}) != 2 or any(label["label"] != clip["adjudicatedLabel"] for label in labs):
                    return bad("DIMENSION")
        metric = c["objectiveMetrics"]
        if metric["eligibleSpeakingMs"] <= 0 or not 0 <= metric["gazeAlignedMs"] <= metric["eligibleSpeakingMs"] or metric["gazeAlignedMs"] / metric["eligibleSpeakingMs"] < 0.8 or metric["maximumOffCameraMs"] > 2000:
            return bad("GAZE")
        if metric["lipOffsetP95Ms"] > 80 or metric["lipOver80MsLongestMs"] > 200:
            return bad("LIP_SYNC")
        if metric["identicalGestureMaxConsecutive"] > 2:
            return bad("GESTURE")
        if metric["captionWordAccuracy"] < 0.98 or abs(metric["captionWordAccuracy"] - (1 - (metric["captionSubstitutions"] + metric["captionDeletions"] + metric["captionInsertions"]) / metric["captionReferenceWords"])) > 1e-12:
            return bad("CAPTION_ACCURACY")
        if metric["captionSpokenWordCoverage"] < 0.98 or abs(metric["captionSpokenWordCoverage"] - (1 - metric["captionDeletions"] / metric["captionReferenceWords"])) > 1e-12:
            return bad("CAPTION_COVERAGE")
        if metric["captionLongestUncaptionedSpeechMs"] > 1000:
            return bad("CAPTION_GAP")
        if metric["contrastRatio"] < 4.5 or not all(metric[k] for k in ("keyboardPassed","screenReaderPassed","visibleFocusPassed","reducedMotionPassed","captionCuePassed","wcagAuditPassed")):
            return bad("ACCESSIBILITY")
        grounding_bad = metric["acceptedUnsupportedClaimCount"] or metric["groundedClaimCitationCoverage"] < 1 or metric["groundedClaimCitedCount"] != metric["groundedClaimCount"]
        grounding_bad |= metric["insufficientContextAbstention"] < 1 or metric["insufficientContextAbstainCount"] != metric["insufficientContextCaseCount"] or "groundingEvidenceSha256" not in metric
        if grounding_bad:
            return bad("GROUNDING")
        review, live = c["defectReview"], c["defectReview"][_LIVE_ROWS]
        if review["adjudicatedSevereDefectCount"] != sum(bool(row[_SEV]) for row in live) or any(row[_SEV] for row in live):
            return bad("SEVERE_DEFECT")
        agree,live_k = _irr(live)
        live_ids_unique = len({row["clipId"] for row in live}) == len(live)
        live_clips_match = {row["clipSha256"] for row in live} == {q[_CLIP_SHA] for q in c["pairs"]}
        live_labels_bad = any(
            {label[_RID] for label in row[_RL]} != qualified
            or len({label["severe"] for label in row[_RL]}) == 1
            and row[_RL][0]["severe"] != row[_SEV]
            for row in live
        )
        live_irr_bad = (abs(review["liveRawAgreement"] - agree) > 1e-12
                        or review["liveKappa"] != live_k
                        or (review["kappaDisposition"] == "MEASURED") != (live_k is not None)
                        or (live_k is not None and live_k < 0.8))
        if review["liveClipCount"] != len(live) or not live_ids_unique or not live_clips_match or live_labels_bad or live_irr_bad:
            return bad("LIVE_IRR")
        if review["adjudicatorId"] in qualified:
            return bad("CALIBRATION")
        if not _retest(c,sample[_VIEWER_MANIFEST]):
            return bad("RETEST")
        if c["decision"] != "PASSED_STATISTICAL":
            return bad("STUDY_DISPOSITION")
    cal_raw,cal_kappa = _irr(cal["rows"])
    class_counts = {name: sum(row[_EXPECTED] == name for row in cal["rows"])
                    for name in ("IDENTITY", "LIMB", "TEMPORAL", "CLEAN")}
    calibration_bad = (
        cal["clipCount"] != len(cal["rows"])
        or len({row["clipId"] for row in cal["rows"]}) != len(cal["rows"])
        or class_counts != {"IDENTITY": 10, "LIMB": 10, "TEMPORAL": 10, "CLEAN": 30}
        or abs(cal["rawAgreement"] - cal_raw) > 1e-12
        or cal["kappa"] != cal_kappa or cal["kappa"] < 0.8
        or not _cal_ok(cal))
    if calibration_bad:
        return bad("CALIBRATION")
    if d["studyDisposition"] == "BYPASSED_BY_HUMAN_OWNER":
        return bad("OWNER_EXCEPTION_UNAUTHORIZED")
    if d["studyDisposition"] != "PASSED_STATISTICAL":
        return bad("STUDY_DISPOSITION")
    if not _valid(d,schema := _read(_GOV / "schemas/cut1-human-realism-evaluation-v1.schema.json"),schema):
        return bad("SCHEMA")
    return ()
def _provider(d: _Doc) -> _Findings:
    def bad(code: str) -> _Findings: return _fail("PROVIDER", code)
    pid = (person := d.get("presenter",{})).get(_PID)
    if pid not in _PPL or person.get("role") != _PPL[pid]["role"]:
        return bad("PRESENTER_ROLE")
    if person.get("assetSha256") != _PPL[pid]["assetSha256"]:
        return bad("ASSET_BINDING")
    if person.get("framing") != _PPL[pid]["framing"] or person.get("gesturesScored") or (_PPL[pid]["handsVisibleReadiness"] == "NOT_READY" and person.get("handsVisible")):
        return bad("FRAMING_READINESS")
    pool: dict[str,tuple[dict[str,Any],str]] = {row["candidateId"]: (row,mode) for group,mode in {"voice": "VOICE","batchVideo": "BATCH_VIDEO","futureQa": "FUTURE_QA"}.items() for row in _read(_GOV / _NAMES[2])[group]}
    cand,mode = pool.get(str(d.get("candidateId")),({},""))
    vendor,trace = d.get("provider",{}),d.get("lineage",{})
    provider_fields_drift = any(
        key in cand and (key != "lifecycle" or cand[key] != "GA_OR_PREVIEW_MUST_PIN")
        and vendor.get(key) != cand[key]
        for key in ("legalEntity", "product", "api", _MODEL, "lifecycle", "role"))
    provider_binding_bad = (
        provider_fields_drift
        or cand.get("lifecycle") == "GA_OR_PREVIEW_MUST_PIN" and vendor.get("lifecycle") not in {"GA", "PREVIEW"}
        or str(vendor.get("version", "")).lower() in {"", "latest", "current", "default", "auto"}
        or not vendor.get(_SOURCES)
        or not set(vendor[_SOURCES]).issubset(cand.get("sources", []))
        or vendor.get("modality") != mode
        or trace.get("providerCandidateId") != d.get("candidateId")
        or any(trace.get(key) != vendor.get(key) for key in (_MODEL, "version", "region")))
    if provider_binding_bad:
        return bad("PROVIDER_BINDING")
    if trace.get(_PID) != pid:
        return bad("LINEAGE")
    idem = d["idempotency"]
    if idem["tenantId"] != trace["tenantId"] or idem[_PROJECT] != trace[_PROJECT] or idem["actorId"] != trace["actorId"]:
        return bad("TENANT_BOUNDARY")
    rights,grant = d["rights"],d["rights"]["consentBinding"]
    if grant[_PID] != pid or grant[_PROJECT] != d["idempotency"][_PROJECT] or vendor["modality"] not in grant["mediaTypes"]:
        return bad("CONSENT_BINDING")
    if (now := _time(d["evaluatedAt"])) is None:
        return bad("SCHEMA")
    consent_at,consent_until = _time(grant["effectiveAt"]),_time(grant["expiresAt"])
    if consent_at is None or consent_until is None or rights["consentStatus"] != "CURRENT" or consent_at > now or consent_until <= now or grant["revokedAt"] is not None:
        return bad("CONSENT_CURRENTNESS")
    if rights["identityCompatibility"] != "VERIFIED" or vendor["identityOrVoiceType"] == "UNVERIFIED" or any(rights[key] != "UNKNOWN" for key in ("commercialUseDecision","derivativeUseDecision")):
        return bad("IDENTITY_COMPATIBILITY")
    if (secret := d["credentialRef"])["scheme"] != "SecretRef" or _re.fullmatch(r"[a-z][a-z0-9_-]*/[a-z][a-z0-9_.-]*",secret["id"]) is None:
        return bad("SECRET_REF")
    required_scans = {"upload","retrievedContext","prompt","transcript","providerPayload","evaluatorPayload"}
    scans = d["screening"]
    bad_scan = any(row["result"] != "CLEAN" or row["tenantId"] != trace["tenantId"] or row[_PROJECT] != trace[_PROJECT] or row["inputType"] != name or row["contentSha256"] != row["contentRef"]["sha256"] for name,row in scans.items())
    if set(scans) != required_scans or bad_scan:
        return bad("SCREENING")
    budget = d["experiment"]
    budget_values = ("maxCalls", "maxSeconds", "maxRetries", "perCallCeilingMicros", "experimentCeilingMicros")
    if d["activation"] != "NONE" or d["authorityEffect"] != "NO_AUTHORITY_EFFECT" or budget["enabled"] or budget["spendState"] != "NOT_AUTHORIZED" or any(budget[key] for key in budget_values) or budget["providerHardCapMicros"] is not None or budget["ownerApprovalRef"] is not None:
        return bad("ACTIVATION")
    if (egress := d["egress"])["enabled"] or egress["endpoint"] != vendor["endpoint"] or egress["method"] != "POST" or egress["redirectsAllowed"] or egress["proxy"] != "NONE" or egress["approvalRef"] is not None:
        return bad("EGRESS")
    if not idem["persistedBeforeEgress"] or idem["requestFingerprint"] != trace["requestPayloadSha256"]:
        return bad("IDEMPOTENCY")
    if idem["state"] != "FAILED_PRE_EGRESS" or idem["reservationDisposition"] != "RELEASED" or idem["egressPossible"] or idem["retryPermitted"]:
        return bad("BILLABLE_UNKNOWN" if idem["state"] in {"BILLABLE_UNKNOWN","FAILED_BILLABLE","COMPLETED"} else "IDEMPOTENCY")
    if (out := d["outputValidation"])["byteCount"] or any(out[key] for key in ("providerSuccess","decoded","schemaValid","contentSafe","activeContentSafe","checksumValid","sizeValid","accepted")):
        return bad("OUTPUT_DISTRUST")
    if not d["disclosure"]["consistent"]:
        return bad("DISCLOSURE")
    if (priv := d["privacy"])["trainingUse"] != "DISABLED_VERIFIED":
        return bad("PRIVACY")
    if priv["processingRegion"] != priv["storageRegion"] and priv["crossBorderTransfer"] == "NONE_VERIFIED":
        return bad("PRIVACY_RESIDENCY")
    if d["observability"]["billableUnits"] or d["observability"]["costMicros"]:
        return bad("BILLABLE_UNKNOWN")
    checks = (vendor["sourceCheckpoint"],rights["governanceCheckpoint"],priv["retentionRef"],priv["backupDeletionRef"],priv["providerDeletionSlaRef"])
    if any(None in (times := tuple(_time(checkpoint[key]) for key in ("accessedAt","effectiveAt","expiresAt"))) or not checkpoint["refreshRequired"] or not (times[1] <= times[0] <= now < times[2]) for checkpoint in checks):
        return bad("PRIVACY_FRESHNESS")
    delete = d["deletion"]
    req, done = _time(delete["requestedAt"]), _time(delete["deletedAt"])
    deletion_state = delete[_PROVIDER_STATE]
    confirmed_ok = (deletion_state == delete[_LOCAL_STATE] == "CONFIRMED"
        and delete["confirmationRef"] is not None and delete["cacheState"] == "INVALIDATED"
        and delete["noResurrection"] and req is not None and done is not None and req <= done <= now)
    not_requested_ok = (deletion_state == delete[_LOCAL_STATE] == "NOT_REQUESTED"
        and delete["providerJobId"] == "not-created"
        and delete["requestedAt"] is None and delete["deletedAt"] is None)
    if not confirmed_ok and not not_requested_ok:
        return bad("DELETION")
    if len(set(d["reproducibility"]["outputSha256s"])) != d["reproducibility"]["repeatCount"]:
        return bad("REPRODUCIBILITY")
    if d["reproducibility"]["selectionDecision"] == "PASS":
        return bad("UNAUTHORIZED_SELECTION")
    if d["eligibility"] != cand.get("eligibility"):
        return bad("FALSE_ELIGIBILITY")
    if not _valid(d,schema := _read(_GOV / "schemas/cut1-presenter-provider-acceptance-v1.schema.json"),schema):
        return bad("SCHEMA")
    return ()
def _safe(scope: str,validator: Any,d: _Doc) -> _Findings:
    try:
        return tuple(validator(d))
    except (AttributeError,IndexError,KeyError,StopIteration,TypeError,ValueError,ZeroDivisionError):
        return _fail(scope,"SCHEMA")
def validate_human_evaluation(d: _Doc) -> _Findings: return _safe("HUMAN",_human,d)
def validate_provider_acceptance(d: _Doc) -> _Findings: return _safe("PROVIDER",_provider,d)
def validate_contract_documents(d: _Doc) -> _Findings:
    if set(d) != set(_NAMES):
        return _fail("BUNDLE","PROTOCOL")
    canonical = {name: _read(_GOV / name) for name in _NAMES}
    if d[_NAMES[0]] != canonical[_NAMES[0]]:
        policy = d[_NAMES[0]].get("exceptionPolicy",{})
        if policy.get("authorizedByThisRoute") or policy.get("ordinaryOrGenericApprovalAccepted"):
            return _fail("BUNDLE","UNAUTHORIZED_EXCEPTION")
        return _fail("BUNDLE","PROTOCOL")
    if d[_NAMES[1]] != canonical[_NAMES[1]]:
        return _fail("BUNDLE","ASSET")
    if d[_NAMES[2]] != canonical[_NAMES[2]]:
        return _fail("BUNDLE","PROVIDER")
    return ()
def _bounded(root: Path,name: str,limit: int) -> bytes:
    path = root
    for part in Path(name).parts:
        path /= part
        if path.is_symlink():
            raise OSError
    if not path.is_file():
        raise OSError
    with path.open("rb") as stream:
        raw = stream.read(limit + 1)
    if len(raw) > limit:
        raise OSError
    return raw
def validate_contract_bundle(root: Path) -> _Findings:
    try:
        old = _bounded(root,"docs/governance/cut1-presenter-contract-red-freeze-v1.json",16384)
        live = _bounded(root,"docs/governance/cut1-presenter-live-binding-v2.json",16384)
        if _hash.sha256(old).hexdigest() != _FREEZE_SHA or _hash.sha256(live).hexdigest() != _LIVE_SHA:
            return _fail("BUNDLE","PROTOCOL")
        hashes = json.loads(live.decode("utf-8"))["immutableInputSha256"]
        raw = {path: _bounded(root,path,65536) for path in hashes}
        if any(_hash.sha256(raw[path]).hexdigest() != want for path,want in hashes.items()):
            return _fail("BUNDLE","PROTOCOL")
        docs = {name: json.loads(raw[f"docs/governance/{name}"].decode("utf-8")) for name in _NAMES}
        return validate_contract_documents(docs)
    except Exception:
        return _fail("BUNDLE","PROTOCOL")
# C4_IMPLEMENTATION_REGION_END


def _load_object(path: Path) -> Mapping[str, Any]:
    parsed = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(parsed, dict):
        raise ValueError("contract input must be a JSON object")
    return parsed


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--kind", choices=("human", "provider", "bundle"), required=True)
    parser.add_argument("--input", type=Path)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args(argv)
    if args.kind == "bundle":
        findings = validate_contract_bundle(args.root)
    else:
        if args.input is None:
            parser.error("--input is required for human/provider validation")
        data = _load_object(args.input)
        findings = (
            validate_human_evaluation(data)
            if args.kind == "human"
            else validate_provider_acceptance(data)
        )
    print(json.dumps([asdict(finding) for finding in findings], sort_keys=True))
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
