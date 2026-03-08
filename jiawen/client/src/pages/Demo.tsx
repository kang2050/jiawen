/**
 * 宠物表情包生成 Demo
 * Design System: Mental Health App — Neumorphism + Accessible & Ethical
 * Palette: Calm Pastels (#F5F2FF base, #8B7CC8 accent, #E8A4C0 pink)
 * Flow: 选择风格 → 上传5张照片 → AI生成 → 查看8张表情包
 */
import { useState, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronLeft, Camera, Sparkles, Download, RotateCcw, Check, Loader2, X, ArrowRight } from "lucide-react";
import { Link } from "wouter";

const API_BASE = "http://localhost:8001";

// ─── Design Tokens (Neumorphism / Calm Pastel) ──────────────────────
const N = {
  bg: "#F5F2FF",
  card: "#F0EDF8",
  shadow: "6px 6px 16px #D0CCEC, -6px -6px 16px #FFFFFF",
  shadowSm: "4px 4px 10px #D0CCEC, -4px -4px 10px #FFFFFF",
  shadowIn: "inset 4px 4px 10px #D0CCEC, inset -4px -4px 10px #FFFFFF",
  shadowInSm: "inset 3px 3px 7px #D0CCEC, inset -3px -3px 7px #FFFFFF",
  accent: "#8B7CC8",
  accentLight: "#B8AEE0",
  pink: "#E8A4C0",
  textDark: "#3D3660",
  textMid: "#6B6490",
  textLight: "#9D99BE",
  radius: "16px",
  radiusSm: "12px",
  radiusLg: "24px",
} as const;

// ─── 4 种风格定义 ────────────────────────────────────────────────────
const STYLES = [
  {
    id: "pixar",
    name: "皮克斯 3D",
    desc: "圆润立体感，毛绒质感，像电影里的动物",
    emoji: "🎬",
    accent: "#F5A55A",
    accentBg: "#FFF5EB",
    accentBorder: "#F5A55A33",
  },
  {
    id: "japanese",
    name: "日系软萌",
    desc: "LINE 贴纸风，厚线条扁平，粉嫩可爱",
    emoji: "🌸",
    accent: "#E890B8",
    accentBg: "#FFF0F6",
    accentBorder: "#E890B833",
  },
  {
    id: "watercolor",
    name: "水彩手绘",
    desc: "温柔水彩插画，像手工画的明信片",
    emoji: "🎨",
    accent: "#6AABCC",
    accentBg: "#EFF8FF",
    accentBorder: "#6AABCC33",
  },
  {
    id: "guochao",
    name: "国潮插画",
    desc: "撞色大胆，传统纹样融合现代设计",
    emoji: "🏮",
    accent: "#E05D45",
    accentBg: "#FFF2EF",
    accentBorder: "#E05D4533",
  },
];

// ─── 5 个拍摄角度引导 ────────────────────────────────────────────────
const PHOTO_SLOTS = [
  { label: "正面", hint: "面朝镜头，全身入画", icon: "🐾" },
  { label: "左侧面", hint: "身体完全侧对镜头", icon: "◀" },
  { label: "右 45°", hint: "斜前方，立体感最佳", icon: "↙" },
  { label: "脸部特写", hint: "眼睛、耳朵清晰可见", icon: "🔍" },
  { label: "背面", hint: "尾巴和背毛纹理", icon: "▶" },
];

// ─── 工具组件：Neu 卡片 ──────────────────────────────────────────────
function NeuCard({ children, style, className = "", onClick }: {
  children: React.ReactNode;
  style?: React.CSSProperties;
  className?: string;
  onClick?: () => void;
}) {
  return (
    <div
      className={className}
      onClick={onClick}
      style={{
        background: N.card,
        borderRadius: N.radius,
        boxShadow: N.shadow,
        ...style,
      }}
    >
      {children}
    </div>
  );
}

// ─── STEP 1: 选择风格 ────────────────────────────────────────────────
function StepStyle({ onNext }: { onNext: (styleId: string) => void }) {
  const [selected, setSelected] = useState<string | null>(null);

  return (
    <div style={{ maxWidth: 600, margin: "0 auto" }}>
      <div style={{ textAlign: "center", marginBottom: 32 }}>
        <span style={{
          display: "inline-block", padding: "6px 16px",
          background: N.accentLight + "33", borderRadius: 20,
          color: N.accent, fontSize: 12, fontWeight: 600, marginBottom: 16,
        }}>第 1 步 · 共 3 步</span>
        <h2 style={{ fontSize: 26, fontWeight: 700, color: N.textDark, marginBottom: 8 }}>选择表情包风格</h2>
        <p style={{ color: N.textMid, fontSize: 14 }}>AI 会按照你选的风格，生成 8 张专属表情包</p>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, marginBottom: 32 }}>
        {STYLES.map((s) => {
          const isSelected = selected === s.id;
          return (
            <motion.div
              key={s.id}
              whileTap={{ scale: 0.97 }}
              onClick={() => setSelected(s.id)}
              style={{
                background: isSelected ? s.accentBg : N.card,
                borderRadius: N.radiusLg,
                boxShadow: isSelected ? `4px 4px 12px ${s.accent}40, -4px -4px 12px #FFFFFF` : N.shadow,
                border: `2px solid ${isSelected ? s.accent : "transparent"}`,
                padding: "20px 18px",
                cursor: "pointer",
                transition: "all 0.25s ease",
                position: "relative",
              }}
            >
              {isSelected && (
                <div style={{
                  position: "absolute", top: 10, right: 10,
                  width: 22, height: 22, borderRadius: "50%",
                  background: s.accent, display: "flex", alignItems: "center", justifyContent: "center",
                }}>
                  <Check size={12} color="#fff" strokeWidth={3} />
                </div>
              )}
              <div style={{ fontSize: 32, marginBottom: 10 }}>{s.emoji}</div>
              <div style={{ fontWeight: 700, color: isSelected ? s.accent : N.textDark, fontSize: 15, marginBottom: 4 }}>
                {s.name}
              </div>
              <div style={{ color: N.textLight, fontSize: 12, lineHeight: 1.5 }}>{s.desc}</div>
            </motion.div>
          );
        })}
      </div>

      <div style={{ textAlign: "center" }}>
        <motion.button
          whileTap={{ scale: 0.97 }}
          onClick={() => selected && onNext(selected)}
          disabled={!selected}
          style={{
            padding: "14px 48px",
            background: selected ? `linear-gradient(135deg, ${N.accent}, ${N.pink})` : "#D0CCEC",
            color: selected ? "#fff" : N.textLight,
            border: "none", borderRadius: 14, fontSize: 15, fontWeight: 700,
            cursor: selected ? "pointer" : "not-allowed",
            boxShadow: selected ? `0 8px 24px ${N.accent}44` : "none",
            transition: "all 0.3s ease",
            display: "inline-flex", alignItems: "center", gap: 8,
          }}
        >
          {selected ? `用「${STYLES.find(s => s.id === selected)?.name}」风格继续` : "请先选择一种风格"}
          {selected && <ArrowRight size={16} />}
        </motion.button>
      </div>
    </div>
  );
}

// ─── STEP 2: 上传照片 ────────────────────────────────────────────────
function StepUpload({
  styleId, onNext,
}: {
  styleId: string;
  onNext: (files: File[], petName: string, petBreed: string) => void;
}) {
  const style = STYLES.find(s => s.id === styleId)!;
  const [photos, setPhotos] = useState<(File | null)[]>(Array(5).fill(null));
  const [previews, setPreviews] = useState<(string | null)[]>(Array(5).fill(null));
  const [petName, setPetName] = useState("");
  const [petBreed, setPetBreed] = useState("");
  const fileInputRefs = useRef<(HTMLInputElement | null)[]>([]);

  const handleFileChange = (idx: number, file: File) => {
    const newPhotos = [...photos];
    const newPreviews = [...previews];
    newPhotos[idx] = file;
    newPreviews[idx] = URL.createObjectURL(file);
    setPhotos(newPhotos);
    setPreviews(newPreviews);
  };

  const removePhoto = (idx: number) => {
    const newPhotos = [...photos];
    const newPreviews = [...previews];
    if (newPreviews[idx]) URL.revokeObjectURL(newPreviews[idx]!);
    newPhotos[idx] = null;
    newPreviews[idx] = null;
    setPhotos(newPhotos);
    setPreviews(newPreviews);
  };

  const uploadedCount = photos.filter(Boolean).length;
  const canProceed = uploadedCount >= 1 && petName.trim().length > 0;

  return (
    <div style={{ maxWidth: 620, margin: "0 auto" }}>
      <div style={{ textAlign: "center", marginBottom: 28 }}>
        <span style={{
          display: "inline-block", padding: "6px 16px",
          background: style.accentBg, borderRadius: 20,
          color: style.accent, fontSize: 12, fontWeight: 600, marginBottom: 16,
          border: `1px solid ${style.accentBorder}`,
        }}>第 2 步 · {style.emoji} {style.name}</span>
        <h2 style={{ fontSize: 26, fontWeight: 700, color: N.textDark, marginBottom: 8 }}>拍 5 张照片，让 AI 认识你的宝贝</h2>
        <p style={{ color: N.textMid, fontSize: 13 }}>角度越多样，生成的表情包越像你家的宝贝 · 至少上传 1 张</p>
      </div>

      {/* 5 个上传槽 */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(5, 1fr)", gap: 10, marginBottom: 24 }}>
        {PHOTO_SLOTS.map((slot, i) => (
          <div key={i}>
            <input
              ref={el => { fileInputRefs.current[i] = el; }}
              type="file" accept="image/*" style={{ display: "none" }}
              onChange={e => e.target.files?.[0] && handleFileChange(i, e.target.files[0])}
            />
            <motion.div
              whileTap={{ scale: 0.96 }}
              onClick={() => !previews[i] && fileInputRefs.current[i]?.click()}
              style={{
                aspectRatio: "1",
                background: previews[i] ? "transparent" : N.card,
                borderRadius: 14,
                boxShadow: previews[i] ? N.shadowIn : N.shadowSm,
                cursor: previews[i] ? "default" : "pointer",
                overflow: "hidden",
                position: "relative",
                transition: "all 0.2s",
              }}
            >
              {previews[i] ? (
                <>
                  <img src={previews[i]!} alt={slot.label} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
                  <button
                    onClick={(e) => { e.stopPropagation(); removePhoto(i); }}
                    style={{
                      position: "absolute", top: 4, right: 4,
                      width: 20, height: 20, borderRadius: "50%",
                      background: "rgba(0,0,0,0.55)", border: "none",
                      display: "flex", alignItems: "center", justifyContent: "center",
                      cursor: "pointer",
                    }}
                  >
                    <X size={10} color="#fff" />
                  </button>
                  <div style={{
                    position: "absolute", bottom: 0, left: 0, right: 0,
                    background: "linear-gradient(transparent, rgba(0,0,0,0.5))",
                    padding: "12px 6px 4px",
                    textAlign: "center",
                  }}>
                    <Check size={10} color="#fff" style={{ display: "inline" }} />
                  </div>
                </>
              ) : (
                <div style={{
                  display: "flex", flexDirection: "column", alignItems: "center",
                  justifyContent: "center", height: "100%", padding: 8, gap: 4,
                }}>
                  <span style={{ fontSize: 18 }}>{slot.icon}</span>
                  <Camera size={14} color={N.accentLight} />
                </div>
              )}
            </motion.div>
            <div style={{ textAlign: "center", marginTop: 6 }}>
              <div style={{ fontSize: 11, fontWeight: 600, color: previews[i] ? style.accent : N.textMid }}>{slot.label}</div>
              <div style={{ fontSize: 10, color: N.textLight, lineHeight: 1.3, marginTop: 2 }}>{slot.hint}</div>
            </div>
          </div>
        ))}
      </div>

      {/* 宠物信息 */}
      <NeuCard style={{ padding: "20px 24px", marginBottom: 24 }}>
        <div style={{ fontSize: 13, fontWeight: 600, color: N.textMid, marginBottom: 14 }}>告诉 AI 一点关于宝贝的信息</div>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14 }}>
          {[
            { label: "宝贝名字 *", value: petName, onChange: setPetName, placeholder: "如：佳文、球球" },
            { label: "品种（可选）", value: petBreed, onChange: setPetBreed, placeholder: "如：边牧、柴犬、橘猫" },
          ].map((field) => (
            <div key={field.label}>
              <label style={{ fontSize: 12, color: N.textMid, display: "block", marginBottom: 6 }}>{field.label}</label>
              <input
                value={field.value}
                onChange={e => field.onChange(e.target.value)}
                placeholder={field.placeholder}
                style={{
                  width: "100%", padding: "10px 14px",
                  background: N.bg, border: "none",
                  borderRadius: N.radiusSm,
                  boxShadow: N.shadowIn,
                  color: N.textDark, fontSize: 13,
                  outline: "none",
                  boxSizing: "border-box",
                }}
              />
            </div>
          ))}
        </div>
      </NeuCard>

      {/* 进度 + 按钮 */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <div style={{ fontSize: 13, color: uploadedCount >= 1 ? style.accent : N.textLight }}>
          已上传 {uploadedCount}/5 张 {uploadedCount >= 1 && "✓"}
        </div>
        <motion.button
          whileTap={{ scale: 0.97 }}
          onClick={() => {
            if (canProceed) {
              const validFiles = photos.filter(Boolean) as File[];
              onNext(validFiles, petName.trim(), petBreed.trim());
            }
          }}
          disabled={!canProceed}
          style={{
            padding: "12px 36px",
            background: canProceed ? `linear-gradient(135deg, ${style.accent}, ${N.accent})` : "#D0CCEC",
            color: canProceed ? "#fff" : N.textLight,
            border: "none", borderRadius: 14, fontSize: 14, fontWeight: 700,
            cursor: canProceed ? "pointer" : "not-allowed",
            boxShadow: canProceed ? `0 6px 20px ${style.accent}44` : "none",
            transition: "all 0.3s",
            display: "inline-flex", alignItems: "center", gap: 8,
          }}
        >
          <Sparkles size={15} />
          开始生成 8 张表情包
        </motion.button>
      </div>
    </div>
  );
}

// ─── STEP 3: 生成中 ──────────────────────────────────────────────────
function StepGenerating({ styleId, petName }: { styleId: string; petName: string }) {
  const style = STYLES.find(s => s.id === styleId)!;
  const expressions = ["哈哈大笑", "撒娇卖萌", "睡着打盹", "超级饿", "生气了", "哇！惊呆了", "爱心满满", "傲娇翻白眼"];

  return (
    <div style={{ maxWidth: 500, margin: "0 auto", textAlign: "center" }}>
      <div style={{ marginBottom: 36 }}>
        <span style={{
          display: "inline-block", padding: "6px 16px",
          background: style.accentBg, borderRadius: 20,
          color: style.accent, fontSize: 12, fontWeight: 600, marginBottom: 20,
          border: `1px solid ${style.accentBorder}`,
        }}>AI 创作中 · {style.emoji} {style.name}</span>

        <div style={{
          width: 80, height: 80, borderRadius: "50%",
          background: N.card, boxShadow: N.shadow,
          display: "flex", alignItems: "center", justifyContent: "center",
          margin: "0 auto 20px",
        }}>
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 3, repeat: Infinity, ease: "linear" }}
          >
            <Sparkles size={32} color={style.accent} />
          </motion.div>
        </div>

        <h2 style={{ fontSize: 22, fontWeight: 700, color: N.textDark, marginBottom: 8 }}>
          正在为{petName}生成专属表情包
        </h2>
        <p style={{ color: N.textMid, fontSize: 13 }}>
          Gemini 3 Pro 正在理解宝贝的颜值特征，稍等片刻...
        </p>
      </div>

      {/* 8 个表情进度 */}
      <NeuCard style={{ padding: "20px 24px" }}>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
          {expressions.map((expr, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0.3 }}
              animate={{ opacity: [0.3, 1, 0.3] }}
              transition={{ duration: 2, repeat: Infinity, delay: i * 0.3 }}
              style={{
                display: "flex", alignItems: "center", gap: 8,
                padding: "8px 12px", borderRadius: 10,
                background: N.bg, boxShadow: N.shadowInSm,
              }}
            >
              <Loader2 size={12} color={style.accent} style={{ flexShrink: 0 }} />
              <span style={{ fontSize: 12, color: N.textMid }}>{expr}</span>
            </motion.div>
          ))}
        </div>
        <p style={{ fontSize: 11, color: N.textLight, marginTop: 14, textAlign: "center" }}>
          每张约 15–30 秒，共 8 张，预计 2–4 分钟
        </p>
      </NeuCard>
    </div>
  );
}

// ─── STEP 4: 结果展示 ────────────────────────────────────────────────
function StepResult({
  stickers, petName, styleId, onRetry,
}: {
  stickers: { expression: string; url: string }[];
  petName: string;
  styleId: string;
  onRetry: () => void;
}) {
  const style = STYLES.find(s => s.id === styleId)!;

  const handleDownload = (url: string, name: string) => {
    const a = document.createElement("a");
    a.href = `${API_BASE}${url}`;
    a.download = `${petName}_${name}.png`;
    a.click();
  };

  const handleDownloadAll = () => {
    stickers.forEach((s, i) => {
      setTimeout(() => handleDownload(s.url, s.expression), i * 300);
    });
  };

  return (
    <div style={{ maxWidth: 680, margin: "0 auto" }}>
      <div style={{ textAlign: "center", marginBottom: 28 }}>
        <span style={{
          display: "inline-block", padding: "6px 16px",
          background: style.accentBg, borderRadius: 20,
          color: style.accent, fontSize: 12, fontWeight: 600, marginBottom: 16,
          border: `1px solid ${style.accentBorder}`,
        }}>✨ 生成完成 · {stickers.length} 张</span>
        <h2 style={{ fontSize: 26, fontWeight: 700, color: N.textDark, marginBottom: 8 }}>
          {petName}的专属表情包来了！
        </h2>
        <p style={{ color: N.textMid, fontSize: 13 }}>风格：{style.emoji} {style.name}</p>
      </div>

      {/* 8 张贴纸网格 */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 14, marginBottom: 28 }}>
        {stickers.map((s, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, scale: 0.85 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: i * 0.08, type: "spring", stiffness: 200 }}
          >
            <NeuCard style={{ overflow: "hidden", position: "relative" }} className="group">
              <img
                src={`${API_BASE}${s.url}`}
                alt={s.expression}
                style={{ width: "100%", aspectRatio: "1", objectFit: "cover", display: "block" }}
              />
              <div style={{ padding: "8px 10px 10px" }}>
                <div style={{ fontSize: 12, fontWeight: 600, color: N.textDark, textAlign: "center" }}>
                  {s.expression}
                </div>
              </div>
              <motion.button
                whileTap={{ scale: 0.9 }}
                onClick={() => handleDownload(s.url, s.expression)}
                style={{
                  position: "absolute", top: 8, right: 8,
                  width: 28, height: 28, borderRadius: "50%",
                  background: "rgba(255,255,255,0.9)",
                  boxShadow: N.shadowSm,
                  border: "none", cursor: "pointer",
                  display: "flex", alignItems: "center", justifyContent: "center",
                }}
              >
                <Download size={13} color={style.accent} />
              </motion.button>
            </NeuCard>
          </motion.div>
        ))}
      </div>

      {/* 操作按钮 */}
      <div style={{ display: "flex", gap: 12, justifyContent: "center", flexWrap: "wrap" }}>
        <motion.button
          whileTap={{ scale: 0.97 }}
          onClick={handleDownloadAll}
          style={{
            padding: "12px 32px",
            background: `linear-gradient(135deg, ${style.accent}, ${N.accent})`,
            color: "#fff", border: "none", borderRadius: 14,
            fontSize: 14, fontWeight: 700, cursor: "pointer",
            boxShadow: `0 6px 20px ${style.accent}44`,
            display: "flex", alignItems: "center", gap: 8,
          }}
        >
          <Download size={16} /> 一键下载全部
        </motion.button>
        <motion.button
          whileTap={{ scale: 0.97 }}
          onClick={onRetry}
          style={{
            padding: "12px 24px",
            background: N.card, color: N.textMid,
            border: "none", borderRadius: 14,
            fontSize: 14, fontWeight: 600, cursor: "pointer",
            boxShadow: N.shadowSm,
            display: "flex", alignItems: "center", gap: 8,
          }}
        >
          <RotateCcw size={15} /> 换个风格再来
        </motion.button>
      </div>
    </div>
  );
}

// ─── 错误结果展示 ────────────────────────────────────────────────────
function StepError({ error, onRetry }: { error: string; onRetry: () => void }) {
  return (
    <div style={{ maxWidth: 480, margin: "0 auto", textAlign: "center" }}>
      <NeuCard style={{ padding: 40 }}>
        <div style={{ fontSize: 48, marginBottom: 16 }}>😔</div>
        <h3 style={{ fontSize: 18, fontWeight: 700, color: N.textDark, marginBottom: 8 }}>生成遇到了问题</h3>
        <p style={{ color: N.textMid, fontSize: 13, marginBottom: 24, lineHeight: 1.6 }}>{error}</p>
        <motion.button
          whileTap={{ scale: 0.97 }}
          onClick={onRetry}
          style={{
            padding: "12px 32px",
            background: `linear-gradient(135deg, ${N.accent}, ${N.pink})`,
            color: "#fff", border: "none", borderRadius: 14,
            fontSize: 14, fontWeight: 700, cursor: "pointer",
            boxShadow: `0 6px 20px ${N.accent}44`,
          }}
        >
          重试一次
        </motion.button>
      </NeuCard>
    </div>
  );
}

// ─── MAIN ────────────────────────────────────────────────────────────
type AppStep = "style" | "upload" | "generating" | "result" | "error";

export default function Demo() {
  const [step, setStep] = useState<AppStep>("style");
  const [styleId, setStyleId] = useState("");
  const [petName, setPetName] = useState("");
  const [stickers, setStickers] = useState<{ expression: string; url: string }[]>([]);
  const [errorMsg, setErrorMsg] = useState("");

  const handleSelectStyle = (id: string) => {
    setStyleId(id);
    setStep("upload");
  };

  const handleUpload = async (files: File[], name: string, breed: string) => {
    setPetName(name);
    setStep("generating");

    try {
      const form = new FormData();
      form.append("pet_name", name);
      form.append("pet_breed", breed);
      form.append("style_id", styleId);
      files.forEach(f => form.append("photos", f));

      const res = await fetch(`${API_BASE}/api/generate`, { method: "POST", body: form });
      if (!res.ok) throw new Error(`服务器错误 ${res.status}`);
      const data = await res.json();

      if (data.stickers && data.stickers.length > 0) {
        setStickers(data.stickers);
        setStep("result");
      } else {
        const errDetail = data.errors?.join("；") || "未生成任何图片";
        throw new Error(errDetail);
      }
    } catch (e: unknown) {
      setErrorMsg(e instanceof Error ? e.message : "未知错误，请稍后重试");
      setStep("error");
    }
  };

  const handleRetry = () => {
    setStep("style");
    setStyleId("");
    setPetName("");
    setStickers([]);
    setErrorMsg("");
  };

  const stepLabel: Record<AppStep, string> = {
    style: "选择风格",
    upload: "上传照片",
    generating: "AI生成中",
    result: "查看结果",
    error: "出错了",
  };

  const stepOrder: AppStep[] = ["style", "upload", "generating", "result"];
  const currentIdx = stepOrder.indexOf(step);

  return (
    <div style={{ minHeight: "100vh", background: N.bg, fontFamily: "'Space Grotesk', 'Noto Sans SC', sans-serif" }}>

      {/* 顶栏 */}
      <div style={{
        position: "fixed", top: 0, left: 0, right: 0, zIndex: 50,
        background: "rgba(245,242,255,0.85)", backdropFilter: "blur(16px)",
        borderBottom: "1px solid #E0DBF5",
        padding: "0 20px",
      }}>
        <div style={{
          maxWidth: 720, margin: "0 auto",
          display: "flex", alignItems: "center", justifyContent: "space-between",
          height: 56,
        }}>
          <Link href="/">
            <span style={{
              display: "flex", alignItems: "center", gap: 6,
              color: N.textMid, fontSize: 13, cursor: "pointer",
              textDecoration: "none",
            }}>
              <ChevronLeft size={16} /> 返回首页
            </span>
          </Link>

          {/* 步骤进度 */}
          <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
            {stepOrder.map((s, i) => (
              <div key={s} style={{ display: "flex", alignItems: "center", gap: 6 }}>
                <div style={{
                  width: 28, height: 28, borderRadius: "50%",
                  background: i < currentIdx ? N.accent : i === currentIdx ? "white" : N.card,
                  boxShadow: i === currentIdx ? `0 0 0 2px ${N.accent}, ${N.shadowSm}` : N.shadowSm,
                  display: "flex", alignItems: "center", justifyContent: "center",
                  transition: "all 0.3s",
                }}>
                  {i < currentIdx
                    ? <Check size={12} color="#fff" strokeWidth={3} />
                    : <span style={{ fontSize: 10, fontWeight: 700, color: i === currentIdx ? N.accent : N.textLight }}>{i + 1}</span>
                  }
                </div>
                {i < stepOrder.length - 1 && (
                  <div style={{
                    width: 24, height: 2, borderRadius: 2,
                    background: i < currentIdx ? N.accent : "#D0CCEC",
                    transition: "background 0.3s",
                  }} />
                )}
              </div>
            ))}
          </div>

          <span style={{ fontSize: 12, color: N.textLight }}>{stepLabel[step]}</span>
        </div>
      </div>

      {/* 内容区 */}
      <div style={{ paddingTop: 80, paddingBottom: 60, padding: "80px 20px 60px" }}>
        <AnimatePresence mode="wait">
          <motion.div
            key={step}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            transition={{ duration: 0.3 }}
          >
            {step === "style" && <StepStyle onNext={handleSelectStyle} />}
            {step === "upload" && <StepUpload styleId={styleId} onNext={handleUpload} />}
            {step === "generating" && <StepGenerating styleId={styleId} petName={petName} />}
            {step === "result" && <StepResult stickers={stickers} petName={petName} styleId={styleId} onRetry={handleRetry} />}
            {step === "error" && <StepError error={errorMsg} onRetry={handleRetry} />}
          </motion.div>
        </AnimatePresence>
      </div>
    </div>
  );
}
