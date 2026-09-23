// 코드모음 텍스트(=====FILE: 제목===== 구획)를 워드로 만든다. 사용: node make_code_docx.js 입력.txt 출력.docx "문서 제목" "부제"
const fs = require("fs");
const { Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType, PageOrientation, LevelFormat, ShadingType, BorderStyle } = require("docx");
const [inp, outp, title, subtitle] = process.argv.slice(2);
const src = fs.readFileSync(inp, "utf8");
const sections = [];
const re = /=====(FILE: )?([^=]+)=====\n([\s\S]*?)(?=\n=====|$)/g;
let m;
while ((m = re.exec(src)) !== null) sections.push({ title: m[2].trim(), body: m[3].replace(/\s+$/, "") });
const CODE_FONT = { ascii: "Consolas", hAnsi: "Consolas", eastAsia: "Malgun Gothic", cs: "Consolas" };
const BODY_FONT = { ascii: "Arial", hAnsi: "Arial", eastAsia: "Malgun Gothic", cs: "Arial" };
const code = text => text.split("\n").map((line, i, arr) => new Paragraph({
  spacing: { before: 0, after: 0, line: 240 },
  shading: { type: ShadingType.CLEAR, fill: "F3F5F8", color: "auto" },
  indent: { left: 120, right: 120 },
  border: i === 0 ? { top: { style: BorderStyle.SINGLE, size: 4, color: "C9CFD8", space: 4 } }
        : i === arr.length - 1 ? { bottom: { style: BorderStyle.SINGLE, size: 4, color: "C9CFD8", space: 4 } } : undefined,
  children: [new TextRun({ text: line === "" ? " " : line, font: CODE_FONT, size: 17, color: line.trim().startsWith("#") ? "6B7280" : "111827" })],
}));
const h = t => new Paragraph({ heading: HeadingLevel.HEADING_1, spacing: { before: 280, after: 120 }, children: [new TextRun({ text: t, font: BODY_FONT })] });
const p = (t, o) => new Paragraph({ spacing: { after: 100 }, children: [new TextRun({ text: t, font: BODY_FONT, size: 20, ...(o || {}) })] });
const bullet = t => new Paragraph({ numbering: { reference: "bullets", level: 0 }, spacing: { after: 60 }, children: [new TextRun({ text: t, font: BODY_FONT, size: 20 })] });
const children = [new Paragraph({ heading: HeadingLevel.TITLE, children: [new TextRun({ text: title, font: BODY_FONT })] })];
if (subtitle) children.push(p(subtitle, { color: "6B7280", size: 18 }));
for (const s of sections) {
  children.push(h(s.title));
  if (s.title === "확인 사항") for (const l of s.body.split("\n").filter(x => x.trim().startsWith("- "))) children.push(bullet(l.trim().slice(2)));
  else children.push(...code(s.body));
}
const doc = new Document({
  styles: { default: { document: { run: { font: BODY_FONT, size: 20 } } } },
  numbering: { config: [{ reference: "bullets", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 480, hanging: 240 } } } }] }] },
  sections: [{ properties: { page: { size: { width: 11906, height: 16838, orientation: PageOrientation.LANDSCAPE }, margin: { top: 850, bottom: 850, left: 900, right: 900 } } }, children }],
});
Packer.toBuffer(doc).then(b => { fs.writeFileSync(outp, b); console.log("written", outp, b.length, "bytes"); });
