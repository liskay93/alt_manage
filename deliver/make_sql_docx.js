const fs = require("fs");
const { Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType, PageOrientation, LevelFormat, ShadingType, BorderStyle } = require("docx");

const src = fs.readFileSync("deliver/01_SQL.txt", "utf8");
// =====FILE: xxx===== 구획으로 나눈다
const sections = [];
const re = /=====(FILE: )?([^=]+)=====\n([\s\S]*?)(?=\n=====|$)/g;
let m;
while ((m = re.exec(src)) !== null) sections.push({ title: m[2].trim(), body: m[3].replace(/\s+$/, "") });

const CODE_FONT = { ascii: "Consolas", hAnsi: "Consolas", eastAsia: "Malgun Gothic", cs: "Consolas" };
const BODY_FONT = { ascii: "Arial", hAnsi: "Arial", eastAsia: "Malgun Gothic", cs: "Arial" };
const GREY = "F3F5F8";

function codeParas(text) {
  return text.split("\n").map((line, i, arr) => new Paragraph({
    spacing: { before: 0, after: 0, line: 240 },
    shading: { type: ShadingType.CLEAR, fill: GREY, color: "auto" },
    indent: { left: 120, right: 120 },
    border: i === 0 ? { top: { style: BorderStyle.SINGLE, size: 4, color: "C9CFD8", space: 4 } }
          : i === arr.length - 1 ? { bottom: { style: BorderStyle.SINGLE, size: 4, color: "C9CFD8", space: 4 } } : undefined,
    children: [new TextRun({ text: line === "" ? " " : line, font: CODE_FONT, size: 17, color: line.trim().startsWith("--") || line.trim().startsWith("#") ? "6B7280" : "111827" })],
  }));
}
function h(text, level) { return new Paragraph({ heading: level, spacing: { before: 280, after: 120 }, children: [new TextRun({ text, font: BODY_FONT })] }); }
function p(text, opts) { return new Paragraph({ spacing: { after: 100 }, children: [new TextRun({ text, font: BODY_FONT, size: 20, ...(opts || {}) })] }); }
function bullet(text) { return new Paragraph({ numbering: { reference: "bullets", level: 0 }, spacing: { after: 60 }, children: [new TextRun({ text, font: BODY_FONT, size: 20 })] }); }

const DESC = {
  "sql/ALT_Fund.sql": "펀드 마스터. FEIAI0488NTA(펀드코드·펀드명·빈티지·통화) + MAAMC0101DTM(ATVT_PGM_FUND_CD → 자산군). Oracle (+) 외부조인",
  "sql/ALT_Commit.sql": "약정 내역. FEIAI0488NTA. AGRT_AMT 는 CURR_CD 통화·단위 1 → KRW 는 억원, 외화는 백만. 외화 원화는 processor 가 약정일 환율로 환산",
  "sql/ALT_PCAP.sql": "집행·분배·NAV 분기 스냅샷. FEIAI0432NTA 최신 제공일 한 벌, GCM 보고 기준, 통화 유형(CD/CP)별 long. 누적값은 processor 가 분기 증분으로 변환",
  "sql/ALT_FX.sql": "환율. FMCBI0006NTA 일별, 1 USD 당 통화 단위. KRW 행 ÷ 통화 행 = 원/1단위 는 processor 가 계산",
};

const children = [
  new Paragraph({ heading: HeadingLevel.TITLE, children: [new TextRun({ text: "ALT_Manage 탭 — SQL 코드모음", font: BODY_FONT })] }),
  p("대체투자 약정·집행·분배·순증 현황 탭의 원재료 쿼리 4개와 노트북 확인 코드입니다. 2026-09-23 수정본 (missing keyword 대응).", { color: "6B7280", size: 18 }),
  p("Oracle 규칙: 세미콜론 없음, 테이블 별명에 AS 없음, ANSI JOIN 대신 (+) 외부조인, 주석은 맨 위 /* */ 한 곳. 파일을 그대로 sql/ 폴더에 넣습니다."),
];
const order = ["sql/ALT_Fund.sql", "sql/ALT_Commit.sql", "sql/ALT_PCAP.sql", "sql/ALT_FX.sql"];
for (const name of order) {
  const s = sections.find(x => x.title === name);
  children.push(h(name, HeadingLevel.HEADING_1));
  if (DESC[name]) children.push(p(DESC[name], { color: "374151" }));
  children.push(...codeParas(s.body));
}
const nb = sections.find(x => x.title.startsWith("노트북 확인 코드"));
children.push(h("노트북 확인 코드", HeadingLevel.HEADING_1));
children.push(p("네 파일을 sql/ 에 넣은 뒤 아래 셀을 순서대로 실행하고, 각 셀의 출력을 그대로 보내 주시면 됩니다."));
children.push(...codeParas(nb.body));
const chk = sections.find(x => x.title === "확인 사항");
children.push(h("확인 사항", HeadingLevel.HEADING_1));
for (const line of chk.body.split("\n").filter(l => l.trim().startsWith("- "))) children.push(bullet(line.trim().slice(2)));

const doc = new Document({
  styles: { default: { document: { run: { font: BODY_FONT, size: 20 } } } },
  numbering: { config: [{ reference: "bullets", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 480, hanging: 240 } } } }] }] },
  sections: [{
    properties: { page: { size: { width: 11906, height: 16838, orientation: PageOrientation.LANDSCAPE }, margin: { top: 850, bottom: 850, left: 900, right: 900 } } },
    children,
  }],
});
Packer.toBuffer(doc).then(buf => { fs.writeFileSync("deliver/01_SQL.docx", buf); console.log("written deliver/01_SQL.docx", buf.length, "bytes"); });
