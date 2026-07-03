import { useState, useRef, useEffect } from "react";
import {
  BookOpen,
  MessageCircle,
  RotateCcw,
  Send,
  CheckSquare,
  Square,
  ChevronRight,
  Lightbulb,
  FileText,
  Award,
  Sparkles,
  Target,
  Layers,
} from "lucide-react";

type Level = "A2" | "B1";
type EssayType = "opinion" | "discussion" | "adv_dis" | "problem_solution" | "two_part_question";
type Section = "introduction" | "body1" | "body2" | "conclusion";
type Tab = "guidance" | "draft" | "score";

interface Message {
  id: string;
  role: "assistant" | "user";
  content: string;
  timestamp: Date;
}

const ESSAY_TYPES: { value: EssayType; label: string; short: string }[] = [
  { value: "opinion", label: "Opinion Essay", short: "Opinion" },
  { value: "discussion", label: "Discussion Essay", short: "Discussion" },
  { value: "adv_dis", label: "Advantages & Disadvantages", short: "Adv/Dis" },
  { value: "problem_solution", label: "Problem & Solution", short: "Problem-Solution" },
  { value: "two_part_question", label: "Two-Part Question", short: "Two-Part" },
];

const SECTIONS: { id: Section; label: string }[] = [
  { id: "introduction", label: "Introduction" },
  { id: "body1", label: "Body 1" },
  { id: "body2", label: "Body 2" },
  { id: "conclusion", label: "Conclusion" },
];

const GUIDANCE_CONTENT: Record<Section, string> = {
  introduction:
    "Phần Introduction gồm 2 phần chính:\n\n**1. Paraphrase đề bài** — Diễn đạt lại câu hỏi bằng từ ngữ của bạn, không copy nguyên văn. Dùng synonyms và đổi cấu trúc câu.\n\n**2. Thesis statement** — Trình bày rõ quan điểm/hướng bài viết của bạn trong 1-2 câu.\n\n💡 *Mẹo*: Bắt đầu bằng câu nền tảng (background sentence) giới thiệu chủ đề trước khi vào paraphrase.",
  body1:
    "Body 1 — Luận điểm chính thứ nhất:\n\n**1. Topic sentence** — Nêu rõ ý chính của đoạn trong câu đầu tiên.\n\n**2. Explanation** — Giải thích tại sao luận điểm đó đúng (1-2 câu).\n\n**3. Example** — Đưa ra ví dụ cụ thể để minh họa.\n\n💡 *Cấu trúc gợi ý*: \"One significant reason is that... This means that... For instance,...\"",
  body2:
    "Body 2 — Luận điểm thứ hai (hoặc phản luận):\n\n**1. Contrasting/Supporting idea** — Nếu là Opinion: thêm một luận điểm ủng hộ. Nếu là Discussion: trình bày quan điểm đối lập.\n\n**2. Development** — Phát triển ý bằng lý giải và dẫn chứng.\n\n💡 *Linking words*: However, On the other hand, Furthermore, Additionally...",
  conclusion:
    "Conclusion — Kết luận ngắn gọn và mạch lạc:\n\n**1. Restate thesis** — Nhắc lại quan điểm chính bằng cách diễn đạt khác (không copy intro).\n\n**2. Summary** — Tóm tắt 2 luận điểm chính trong 1 câu.\n\n**3. Final thought** (tùy chọn) — Có thể thêm khuyến nghị hoặc nhận định tổng quát.\n\n💡 *Lưu ý*: Không đưa thông tin mới vào conclusion.",
};

const WELCOME_MESSAGE: Message = {
  id: "welcome",
  role: "assistant",
  content:
    "Chào bạn! 👋 Mình là Essay Writing Coach — trợ lý hướng dẫn viết IELTS Writing Task 2 bằng tiếng Việt.\n\nHãy paste đề bài IELTS Writing Task 2 vào đây để bắt đầu. Mình sẽ hướng dẫn bạn từng bước từ Introduction đến Conclusion.",
  timestamp: new Date(),
};

function formatMessage(content: string) {
  const parts = content.split(/(\*\*[^*]+\*\*)/g);
  return parts.map((part, i) => {
    if (part.startsWith("**") && part.endsWith("**")) {
      return <strong key={i}>{part.slice(2, -2)}</strong>;
    }
    return <span key={i}>{part}</span>;
  });
}

export default function App() {
  const [sessionId] = useState(() => Math.random().toString(36).substring(7));
  const [essayType, setEssayType] = useState<EssayType | null>(null);
  const [level, setLevel] = useState<Level>("B1");
  const [completedSections, setCompletedSections] = useState<Set<Section>>(new Set());
  const [activeSection, setActiveSection] = useState<Section>("introduction");
  const [messages, setMessages] = useState<Message[]>([WELCOME_MESSAGE]);
  const [input, setInput] = useState("");
  const [activeTab, setActiveTab] = useState<Tab>("guidance");
  const [draft, setDraft] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  
  // Real-time coach guidelines states
  const [paraphrases, setParaphrases] = useState<{ text: string; technique: string }[]>([]);
  const [vocabulary, setVocabulary] = useState<{ word: string; meaning?: string; example: string }[]>([]);
  const [structures, setStructures] = useState<{ pattern?: string; text: string; explanation?: string }[]>([]);
  const [instructions, setInstructions] = useState<string[]>([]);
  const [template, setTemplate] = useState<string>("");
  const [example, setExample] = useState<string>("");
  const [checklist, setChecklist] = useState<string[]>([]);
  const [checkedItems, setCheckedItems] = useState<Record<string, boolean>>({});

  // Real-time evaluation states
  const [evaluation, setEvaluation] = useState<any | null>(null);
  const [isEvaluating, setIsEvaluating] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isTyping]);

  // Auto-resize input textarea to fit content dynamically
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  }, [input]);


  async function handleSend() {
    if (!input.trim()) return;
    const userMsg: Message = {
      id: Date.now().toString(),
      role: "user",
      content: input.trim(),
      timestamp: new Date(),
    };
    setMessages((m) => [...m, userMsg]);
    setInput("");
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
    setIsTyping(true);

    try {
      const apiUrl = import.meta.env.VITE_API_URL || "http://localhost:8000";
      const response = await fetch(`${apiUrl}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: userMsg.content,
          session_id: sessionId,
          user_id: "react_user",
          level: level,
        }),
      });
      const data = await response.json();
      
      const assistantMsg: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: data.text,
        timestamp: new Date(),
      };
      setMessages((m) => [...m, assistantMsg]);
      
      // Process tool calls from ADK
      if (data.tool_calls) {
        for (const tc of data.tool_calls) {
          const { tool, result } = tc;
          if (!result) continue;

          if (tool === "classify_essay_type") {
            setEssayType(result.essay_type);
          } else if (tool === "paraphrase_prompt") {
            if (result.paraphrases) {
              setParaphrases(result.paraphrases);
            }
          } else if (tool === "guide_essay_section") {
            if (result.instructions) setInstructions(result.instructions);
            if (result.template) setTemplate(result.template);
            if (result.example) setExample(result.example);
            if (result.useful_phrases) {
              setParaphrases(result.useful_phrases.map((p: string) => ({ text: p, technique: "Useful Phrase" })));
            }
            if (result.checklist) {
              setChecklist(result.checklist);
              setCheckedItems({});
            }
            if (result.section) {
              setActiveSection(result.section);
            }
          } else if (tool === "suggest_sentence_structures") {
            if (result.variations) setStructures(result.variations);
          } else if (tool === "enrich_vocabulary") {
            let vocabList: any[] = [];
            if (result.suggestions) {
              for (const word of Object.keys(result.suggestions)) {
                vocabList.push(...result.suggestions[word].map((item: any) => ({
                  word: item.word,
                  meaning: item.meaning_vi,
                  example: item.example
                })));
              }
            }
            if (result.topic_words) {
              vocabList.push(...result.topic_words.map((item: any) => ({
                word: item.word,
                meaning: item.meaning_vi,
                example: item.example
              })));
            }
            if (vocabList.length > 0) {
              setVocabulary(vocabList);
            }
          }
        }
      }
    } catch (err) {
      console.error(err);
      const errorMsg: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: "⚠️ Đã xảy ra lỗi kết nối với máy chủ AI. Vui lòng thử lại sau.",
        timestamp: new Date(),
      };
      setMessages((m) => [...m, errorMsg]);
    } finally {
      setIsTyping(false);
    }
  }

  async function handleEvaluate() {
    if (!draft.trim()) return;
    setIsEvaluating(true);
    setEvaluation(null);

    try {
      const apiUrl = import.meta.env.VITE_API_URL || "http://localhost:8000";
      const response = await fetch(`${apiUrl}/api/evaluate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          essay_text: draft.trim(),
          essay_type: essayType || "opinion",
        }),
      });
      const data = await response.json();
      if (data.error) {
        alert(data.message || "Lỗi khi chấm điểm.");
      } else {
        setEvaluation(data);
      }
    } catch (err) {
      console.error(err);
      alert("⚠️ Lỗi kết nối máy chủ chấm điểm.");
    } finally {
      setIsEvaluating(false);
    }
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }

  function handleReset() {
    setMessages([WELCOME_MESSAGE]);
    setEssayType(null);
    setCompletedSections(new Set());
    setActiveSection("introduction");
    setDraft("");
    setInput("");
    setActiveTab("guidance");
    setParaphrases([]);
    setVocabulary([]);
    setStructures([]);
    setInstructions([]);
    setTemplate("");
    setExample("");
    setChecklist([]);
    setCheckedItems({});
    setEvaluation(null);
  }

  function toggleSection(section: Section) {
    setCompletedSections((s) => {
      const next = new Set(s);
      if (next.has(section)) next.delete(section);
      else next.add(section);
      return next;
    });
  }

  function toggleChecklistItem(item: string) {
    setCheckedItems((prev) => {
      const updated = { ...prev, [item]: !prev[item] };
      const allCompleted = checklist.every((c) => updated[c]);
      if (allCompleted) {
        setCompletedSections((prevSet) => {
          const nextSet = new Set(prevSet);
          nextSet.add(activeSection);
          return nextSet;
        });
      } else {
        setCompletedSections((prevSet) => {
          const nextSet = new Set(prevSet);
          nextSet.delete(activeSection);
          return nextSet;
        });
      }
      return updated;
    });
  }

  const progressPct = (completedSections.size / SECTIONS.length) * 100;

  return (
    <div
      className="h-screen w-full flex flex-col overflow-hidden"
      style={{ fontFamily: "'Inter', sans-serif", background: "var(--background)" }}
    >
      {/* Top bar */}
      <header
        className="flex items-center justify-between px-6 py-3 border-b shrink-0"
        style={{ borderColor: "var(--border)", background: "var(--card)" }}
      >
        <div className="flex items-center gap-3">
          <div
            className="w-8 h-8 rounded-lg flex items-center justify-center"
            style={{ background: "var(--primary)" }}
          >
            <BookOpen size={16} color="var(--primary-foreground)" />
          </div>
          <div>
            <h1
              className="text-sm font-semibold tracking-tight leading-none"
              style={{ fontFamily: "'Playfair Display', serif", color: "var(--foreground)" }}
            >
              Essay Writing Coach
            </h1>
            <p className="text-xs mt-0.5" style={{ color: "var(--muted-foreground)" }}>
              IELTS Writing Task 2 · AI hướng dẫn tiếng Việt
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {essayType && (
            <span
              className="text-xs px-2.5 py-1 rounded-full font-medium"
              style={{ background: "var(--secondary)", color: "var(--foreground)" }}
            >
              {ESSAY_TYPES.find((t) => t.value === essayType)?.short}
            </span>
          )}
          <span
            className="text-xs px-2.5 py-1 rounded-full font-medium"
            style={{ background: "var(--primary)", color: "var(--primary-foreground)" }}
          >
            {level}
          </span>
        </div>
      </header>

      {/* Main layout */}
      <div className="flex flex-1 min-h-0">
        {/* Sidebar */}
        <aside
          className="w-56 shrink-0 flex flex-col border-r overflow-y-auto"
          style={{ background: "var(--sidebar)", borderColor: "var(--sidebar-border)" }}
        >
          <div className="p-4 flex flex-col gap-5 flex-1">
            {/* Essay type */}
            <div>
              <p
                className="text-xs font-semibold uppercase tracking-widest mb-2.5"
                style={{ color: "var(--muted-foreground)" }}
              >
                Dạng đề
              </p>
              <div className="flex flex-col gap-1">
                {ESSAY_TYPES.map((t) => (
                  <button
                    key={t.value}
                    onClick={() => setEssayType(t.value)}
                    className="text-left text-xs px-2.5 py-1.5 rounded-md transition-all duration-150 flex items-center gap-2"
                    style={{
                      background: essayType === t.value ? "var(--primary)" : "transparent",
                      color: essayType === t.value ? "var(--primary-foreground)" : "var(--foreground)",
                      fontWeight: essayType === t.value ? 500 : 400,
                    }}
                  >
                    {essayType === t.value && <ChevronRight size={10} />}
                    {t.short}
                  </button>
                ))}
              </div>
            </div>

            {/* Level */}
            <div>
              <p
                className="text-xs font-semibold uppercase tracking-widest mb-2.5"
                style={{ color: "var(--muted-foreground)" }}
              >
                Trình độ
              </p>
              <div className="flex gap-1.5">
                {(["A2", "B1"] as Level[]).map((l) => (
                  <button
                    key={l}
                    onClick={() => setLevel(l)}
                    className="flex-1 text-xs py-1.5 rounded-md font-medium transition-all duration-150"
                    style={{
                      background: level === l ? "var(--accent)" : "var(--muted)",
                      color: level === l ? "var(--foreground)" : "var(--muted-foreground)",
                      border: level === l ? "1.5px solid var(--accent)" : "1.5px solid transparent",
                    }}
                  >
                    {l}
                  </button>
                ))}
              </div>
            </div>

            {/* Progress */}
            <div>
              <div className="flex items-center justify-between mb-2.5">
                <p
                  className="text-xs font-semibold uppercase tracking-widest"
                  style={{ color: "var(--muted-foreground)" }}
                >
                  Tiến độ
                </p>
                <span className="text-xs font-medium" style={{ color: "var(--primary)" }}>
                  {completedSections.size}/{SECTIONS.length}
                </span>
              </div>

              {/* Progress bar */}
              <div
                className="h-1 rounded-full mb-3 overflow-hidden"
                style={{ background: "var(--muted)" }}
              >
                <div
                  className="h-full rounded-full transition-all duration-500"
                  style={{ width: `${progressPct}%`, background: "var(--primary)" }}
                />
              </div>

              <div className="flex flex-col gap-1.5">
                {SECTIONS.map((s) => {
                  const done = completedSections.has(s.id);
                  const active = activeSection === s.id;
                  return (
                    <button
                      key={s.id}
                      onClick={() => {
                        setActiveSection(s.id);
                        setActiveTab("guidance");
                        toggleSection(s.id);
                      }}
                      className="flex items-center gap-2.5 text-xs py-1.5 px-2 rounded-md text-left transition-all duration-150"
                      style={{
                        background: active ? "var(--sidebar-accent)" : "transparent",
                        color: done
                          ? "var(--primary)"
                          : active
                          ? "var(--foreground)"
                          : "var(--muted-foreground)",
                      }}
                    >
                      {done ? (
                        <CheckSquare size={13} style={{ color: "var(--primary)" }} />
                      ) : (
                        <Square size={13} />
                      )}
                      <span className={done ? "line-through" : ""}>{s.label}</span>
                    </button>
                  );
                })}
              </div>
            </div>
          </div>

          {/* Reset button */}
          <div className="p-4 border-t" style={{ borderColor: "var(--sidebar-border)" }}>
            <button
              onClick={handleReset}
              className="w-full flex items-center justify-center gap-2 text-xs py-2 rounded-md transition-all duration-150 font-medium"
              style={{
                background: "var(--muted)",
                color: "var(--muted-foreground)",
              }}
              onMouseEnter={(e) => {
                (e.currentTarget as HTMLButtonElement).style.background = "var(--destructive)";
                (e.currentTarget as HTMLButtonElement).style.color = "var(--destructive-foreground)";
              }}
              onMouseLeave={(e) => {
                (e.currentTarget as HTMLButtonElement).style.background = "var(--muted)";
                (e.currentTarget as HTMLButtonElement).style.color = "var(--muted-foreground)";
              }}
            >
              <RotateCcw size={12} />
              Bắt đầu lại
            </button>
          </div>
        </aside>

        {/* Chat panel */}
        <main
          className="flex flex-col flex-1 min-w-0 border-r"
          style={{ borderColor: "var(--border)" }}
        >
          {/* Chat header */}
          <div
            className="flex items-center gap-2.5 px-5 py-3.5 border-b shrink-0"
            style={{ borderColor: "var(--border)", background: "var(--card)" }}
          >
            <MessageCircle size={15} style={{ color: "var(--primary)" }} />
            <span
              className="text-sm font-semibold"
              style={{ fontFamily: "'Playfair Display', serif", color: "var(--foreground)" }}
            >
              Chat
            </span>
            <span
              className="ml-auto text-xs px-2 py-0.5 rounded-full"
              style={{ background: "var(--secondary)", color: "var(--muted-foreground)" }}
            >
              {SECTIONS.find((s) => s.id === activeSection)?.label}
            </span>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto px-5 py-4 flex flex-col gap-4">
            {messages.map((msg) => (
              <div
                key={msg.id}
                className={`flex gap-3 ${msg.role === "user" ? "flex-row-reverse" : "flex-row"}`}
              >
                {msg.role === "assistant" && (
                  <div
                    className="w-7 h-7 rounded-full flex items-center justify-center shrink-0 mt-0.5"
                    style={{ background: "var(--primary)" }}
                  >
                    <Sparkles size={12} color="var(--primary-foreground)" />
                  </div>
                )}
                <div
                  className="max-w-[78%] px-4 py-3 rounded-2xl text-sm leading-relaxed whitespace-pre-line"
                  style={{
                    background:
                      msg.role === "assistant" ? "var(--card)" : "var(--primary)",
                    color:
                      msg.role === "assistant" ? "var(--foreground)" : "var(--primary-foreground)",
                    border: msg.role === "assistant" ? "1px solid var(--border)" : "none",
                    borderRadius:
                      msg.role === "assistant" ? "4px 18px 18px 18px" : "18px 4px 18px 18px",
                  }}
                >
                  {formatMessage(msg.content)}
                </div>
              </div>
            ))}

            {isTyping && (
              <div className="flex gap-3">
                <div
                  className="w-7 h-7 rounded-full flex items-center justify-center shrink-0"
                  style={{ background: "var(--primary)" }}
                >
                  <Sparkles size={12} color="var(--primary-foreground)" />
                </div>
                <div
                  className="px-4 py-3 rounded-2xl flex items-center gap-1"
                  style={{
                    background: "var(--card)",
                    border: "1px solid var(--border)",
                    borderRadius: "4px 18px 18px 18px",
                  }}
                >
                  {[0, 1, 2].map((i) => (
                    <span
                      key={i}
                      className="w-1.5 h-1.5 rounded-full"
                      style={{
                        background: "var(--muted-foreground)",
                        animation: `bounce 1.2s ease-in-out ${i * 0.2}s infinite`,
                      }}
                    />
                  ))}
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input */}
          <div
            className="shrink-0 p-4 border-t"
            style={{ borderColor: "var(--border)", background: "var(--card)" }}
          >
            <div
              className="flex items-end gap-3 rounded-xl p-3"
              style={{ background: "var(--input-background)", border: "1px solid var(--border)" }}
            >
              <textarea
                ref={textareaRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Nhập đề bài hoặc câu hỏi của bạn… (Enter để gửi)"
                rows={1}
                className="flex-1 resize-none bg-transparent outline-none text-sm leading-relaxed"
                style={{
                  color: "var(--foreground)",
                  fontFamily: "'Inter', sans-serif",
                  maxHeight: "120px",
                  overflow: "auto",
                }}
              />
              <button
                onClick={handleSend}
                disabled={!input.trim() || isTyping}
                className="w-8 h-8 rounded-lg flex items-center justify-center shrink-0 transition-all duration-150"
                style={{
                  background: input.trim() && !isTyping ? "var(--primary)" : "var(--muted)",
                  color: input.trim() && !isTyping ? "var(--primary-foreground)" : "var(--muted-foreground)",
                }}
              >
                <Send size={13} />
              </button>
            </div>
            <p className="text-xs mt-2 text-center" style={{ color: "var(--muted-foreground)" }}>
              Shift+Enter để xuống dòng
            </p>
          </div>
        </main>

        {/* Results panel */}
        <section className="w-80 shrink-0 flex flex-col" style={{ background: "var(--card)" }}>
          {/* Results header */}
          <div
            className="flex items-center gap-2.5 px-5 py-3.5 border-b shrink-0"
            style={{ borderColor: "var(--border)" }}
          >
            <Layers size={15} style={{ color: "var(--primary)" }} />
            <span
              className="text-sm font-semibold"
              style={{ fontFamily: "'Playfair Display', serif", color: "var(--foreground)" }}
            >
              Kết quả
            </span>
          </div>

          {/* Tabs */}
          <div
            className="flex border-b shrink-0"
            style={{ borderColor: "var(--border)" }}
          >
            {(
              [
                { id: "guidance" as Tab, icon: Lightbulb, label: "Hướng dẫn" },
                { id: "draft" as Tab, icon: FileText, label: "Bài viết" },
                { id: "score" as Tab, icon: Award, label: "Chấm điểm" },
              ] as const
            ).map(({ id, icon: Icon, label }) => (
              <button
                key={id}
                onClick={() => setActiveTab(id)}
                className="flex-1 flex items-center justify-center gap-1.5 text-xs py-3 font-medium transition-all duration-150 border-b-2"
                style={{
                  borderBottomColor: activeTab === id ? "var(--primary)" : "transparent",
                  color: activeTab === id ? "var(--primary)" : "var(--muted-foreground)",
                  background: "transparent",
                }}
              >
                <Icon size={12} />
                {label}
              </button>
            ))}
          </div>

          {/* Tab content */}
          <div className="flex-1 overflow-y-auto">
            {activeTab === "guidance" && (
              <div className="p-5">
                {/* Section pills */}
                <div className="flex gap-1.5 flex-wrap mb-4">
                  {SECTIONS.map((s) => (
                    <button
                      key={s.id}
                      onClick={() => setActiveSection(s.id)}
                      className="text-xs px-2.5 py-1 rounded-full transition-all duration-150 font-medium"
                      style={{
                        background:
                          activeSection === s.id ? "var(--primary)" : "var(--secondary)",
                        color:
                          activeSection === s.id
                            ? "var(--primary-foreground)"
                            : "var(--muted-foreground)",
                      }}
                    >
                      {s.label}
                    </button>
                  ))}
                </div>

                {/* Dynamic Instructions */}
                {instructions.length > 0 ? (
                  <div className="flex flex-col gap-2 mb-4">
                    <p className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">Các bước viết phần {activeSection}:</p>
                    <div className="flex flex-col gap-1.5">
                      {instructions.map((step, idx) => (
                        <div key={idx} className="text-xs leading-relaxed p-2.5 rounded-lg bg-secondary text-foreground">
                          {idx + 1}. {formatMessage(step)}
                        </div>
                      ))}
                    </div>
                  </div>
                ) : (
                  <div
                    className="text-xs leading-relaxed whitespace-pre-line rounded-xl p-4 mb-4"
                    style={{
                      background: "var(--secondary)",
                      color: "var(--foreground)",
                      lineHeight: 1.8,
                    }}
                  >
                    {formatMessage(GUIDANCE_CONTENT[activeSection])}
                  </div>
                )}

                {/* Dynamic Template & Example */}
                {template && (
                  <div className="mb-4">
                    <p className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground mb-1">Mẫu câu gợi ý (Template):</p>
                    <pre className="text-xs p-3 rounded-xl bg-secondary whitespace-pre-wrap text-foreground font-mono leading-relaxed border border-border">
                      {template}
                    </pre>
                  </div>
                )}
                {example && (
                  <div className="mb-4">
                    <p className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground mb-1">Ví dụ hoàn chỉnh:</p>
                    <div className="text-xs p-3 rounded-xl bg-secondary leading-relaxed text-foreground border border-border">
                      {example}
                    </div>
                  </div>
                )}

                {/* Dynamic Checklist */}
                {checklist.length > 0 && (
                  <div className="mb-4 p-3 rounded-xl border border-border bg-card">
                    <p className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground mb-2">Checklist tự kiểm tra:</p>
                    <div className="flex flex-col gap-2">
                      {checklist.map((item, idx) => {
                        const checked = checkedItems[item] || false;
                        return (
                          <button
                            key={idx}
                            onClick={() => toggleChecklistItem(item)}
                            className="flex items-start gap-2.5 text-xs text-left w-full"
                          >
                            {checked ? (
                              <CheckSquare size={13} className="text-primary mt-0.5 shrink-0" />
                            ) : (
                              <Square size={13} className="text-muted-foreground mt-0.5 shrink-0" />
                            )}
                            <span className={checked ? "line-through text-muted-foreground" : "text-foreground"}>
                              {item}
                            </span>
                          </button>
                        );
                      })}
                    </div>
                  </div>
                )}

                {/* Paraphrases list */}
                <div className="mb-4 border-t border-border pt-3">
                  <p className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground mb-2">🔄 Cụm từ có thể paraphrase:</p>
                  {paraphrases.length > 0 ? (
                    <div className="flex flex-col gap-2">
                      {paraphrases.map((p, idx) => (
                        <div key={idx} className="p-2.5 rounded-lg border border-border bg-card">
                          <p className="text-[10px] text-muted-foreground uppercase font-bold">{p.technique}</p>
                          <p className="text-xs text-foreground mt-0.5">{p.text}</p>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-xs text-muted-foreground italic">Chưa có gợi ý — nhập đề bài để tự động nhận gợi ý.</p>
                  )}
                </div>

                {/* Vocabulary suggestions */}
                <div className="mb-4 border-t border-border pt-3">
                  <p className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground mb-2">📚 Từ vựng thay thế:</p>
                  {vocabulary.length > 0 ? (
                    <div className="flex flex-col gap-1.5">
                      {vocabulary.map((v, idx) => (
                        <div key={idx} className="text-xs leading-relaxed text-foreground">
                          • <strong>{v.word}</strong> {v.meaning ? `(${v.meaning})` : ""} — <em>{v.example}</em>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-xs text-muted-foreground italic">Chưa có từ vựng — hỏi agent để cải thiện.</p>
                  )}
                </div>

                {/* Sentence structures suggestions */}
                <div className="mb-4 border-t border-border pt-3">
                  <p className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground mb-2">🏗️ Cấu trúc câu có thể dùng:</p>
                  {structures.length > 0 ? (
                    <div className="flex flex-col gap-3">
                      {structures.map((s, idx) => (
                        <div key={idx} className="p-2.5 rounded-lg border border-border bg-card">
                          {s.pattern && <p className="text-[10px] text-primary font-mono font-bold">{s.pattern}</p>}
                          <p className="text-xs text-foreground mt-0.5">{s.text}</p>
                          {s.explanation && <p className="text-[10px] text-muted-foreground mt-1">{s.explanation}</p>}
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-xs text-muted-foreground italic">Chưa có cấu trúc câu — hỏi agent để nhận gợi ý.</p>
                  )}
                </div>

                {/* Tips */}
                <div
                  className="mt-4 p-3 rounded-xl flex gap-2.5"
                  style={{ background: "#fef9ee", border: "1px solid #f0d080" }}
                >
                  <Target size={13} style={{ color: "#b87c2e", marginTop: 1, shrink: 0 }} />
                  <p className="text-xs leading-relaxed" style={{ color: "#7a5222" }}>
                    Gõ câu hỏi vào chat để nhận phản hồi chi tiết từ AI Coach theo trình độ{" "}
                    <strong>{level}</strong>.
                  </p>
                </div>
              </div>
            )}

            {activeTab === "draft" && (
              <div className="p-5 flex flex-col gap-3 h-full">
                <p className="text-xs" style={{ color: "var(--muted-foreground)" }}>
                  Viết bài hoàn chỉnh của bạn ở đây để lưu và chấm điểm.
                </p>
                <textarea
                  value={draft}
                  onChange={(e) => setDraft(e.target.value)}
                  placeholder="Paste hoặc viết bài essay của bạn vào đây…"
                  className="flex-1 w-full resize-none rounded-xl p-4 text-xs leading-relaxed outline-none transition-all"
                  style={{
                    background: "var(--secondary)",
                    color: "var(--foreground)",
                    border: "1px solid var(--border)",
                    fontFamily: "'Inter', sans-serif",
                    minHeight: "280px",
                  }}
                />
                {draft && (
                  <div
                    className="flex items-center justify-between text-xs py-2 px-3 rounded-lg"
                    style={{ background: "var(--muted)", color: "var(--muted-foreground)" }}
                  >
                    <span>{draft.split(/\s+/).filter(Boolean).length} từ</span>
                    <span>{draft.length} ký tự</span>
                  </div>
                )}
              </div>
            )}

            {activeTab === "score" && (
              <div className="p-5">
                {!draft ? (
                  <div
                    className="rounded-xl p-6 text-center flex flex-col items-center gap-3"
                    style={{ background: "var(--secondary)" }}
                  >
                    <Award size={28} style={{ color: "var(--muted-foreground)" }} />
                    <p className="text-xs leading-relaxed" style={{ color: "var(--muted-foreground)" }}>
                      Hãy viết bài essay trong tab{" "}
                      <strong style={{ color: "var(--foreground)" }}>Bài viết</strong> trước để mình
                      có thể chấm điểm.
                    </p>
                  </div>
                ) : (
                  <div className="flex flex-col gap-4">
                    <button
                      onClick={handleEvaluate}
                      disabled={isEvaluating}
                      className="w-full text-xs font-semibold py-2.5 rounded-lg transition-all duration-150 flex items-center justify-center gap-2"
                      style={{
                        background: "var(--primary)",
                        color: "var(--primary-foreground)",
                      }}
                    >
                      <Sparkles size={13} />
                      {isEvaluating ? "Đang chấm điểm..." : "Chấm điểm bài viết"}
                    </button>

                    {isEvaluating && (
                      <div className="text-center py-4">
                        <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-primary mx-auto"></div>
                        <p className="text-xs text-muted-foreground mt-2">Hệ thống đang phân tích bài viết của bạn...</p>
                      </div>
                    )}

                    {!isEvaluating && evaluation && (
                      <div className="flex flex-col gap-4">
                        <div
                          className="p-3 rounded-xl text-center"
                          style={{ background: "var(--primary)" }}
                        >
                          <p className="text-xs" style={{ color: "var(--primary-foreground)", opacity: 0.75 }}>
                            Band ước tính
                          </p>
                          <p
                            className="text-2xl font-bold mt-0.5"
                            style={{
                              color: "var(--primary-foreground)",
                              fontFamily: "'Playfair Display', serif",
                            }}
                          >
                            {evaluation.overall_band} / 6.5
                          </p>
                          <p className="text-[10px] text-primary-foreground/60 mt-1">
                            Dạng bài: {evaluation.essay_type} | Từ: {evaluation.word_count}
                          </p>
                        </div>

                        {/* Criteria list */}
                        {[
                          { key: "task_response", label: "Task Achievement (Đáp ứng yêu cầu)" },
                          { key: "coherence_cohesion", label: "Coherence & Cohesion (Mạch lạc)" },
                          { key: "lexical_resource", label: "Lexical Resource (Từ vựng)" },
                          { key: "grammatical_range", label: "Grammar Range (Ngữ pháp)" },
                        ].map(({ key, label }) => {
                          const crit = evaluation.criteria[key] || { band: 1.0, feedback: "", suggestions: [] };
                          return (
                            <div key={key} className="p-3 rounded-xl border border-border bg-card">
                              <div className="flex justify-between items-baseline mb-1">
                                <span className="text-xs font-semibold" style={{ color: "var(--foreground)" }}>
                                  {label}
                                </span>
                                <span
                                  className="text-xs font-semibold text-primary"
                                  style={{ fontFamily: "'DM Mono', monospace" }}
                                >
                                  {crit.band}/6.5
                                </span>
                              </div>
                              
                              {/* Progress bar */}
                              <div className="h-1.5 rounded-full overflow-hidden bg-muted mb-2">
                                <div
                                  className="h-full rounded-full bg-primary"
                                  style={{ width: `${(crit.band / 6.5) * 100}%` }}
                                />
                              </div>

                              <p className="text-[11px] leading-relaxed text-foreground mt-1.5">
                                <strong>Nhận xét:</strong> {crit.feedback}
                              </p>
                              {crit.suggestions && crit.suggestions.length > 0 && (
                                <div className="mt-2 text-[10px] leading-relaxed text-muted-foreground">
                                  <strong>Gợi ý cải thiện:</strong>
                                  <ul className="list-disc pl-3 mt-0.5 space-y-0.5">
                                    {crit.suggestions.map((s: string, idx: number) => (
                                      <li key={idx}>{s}</li>
                                    ))}
                                  </ul>
                                </div>
                              )}
                            </div>
                          );
                        })}
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>
        </section>
      </div>

      <style>{`
        @keyframes bounce {
          0%, 60%, 100% { transform: translateY(0); }
          30% { transform: translateY(-5px); }
        }
        textarea::placeholder { color: var(--muted-foreground); opacity: 0.7; }
        ::-webkit-scrollbar { width: 4px; height: 4px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: var(--border); border-radius: 999px; }
        ::-webkit-scrollbar-thumb:hover { background: var(--muted-foreground); }
      `}</style>
    </div>
  );
}
