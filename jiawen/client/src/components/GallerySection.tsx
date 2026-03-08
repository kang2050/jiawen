// Design: Mental Health App · 效果展示 · 原图 → 表情包对比
import { motion, AnimatePresence } from "framer-motion";
import { useScrollAnimation } from "@/hooks/useScrollAnimation";
import { X, Sparkles } from "lucide-react";
import { useState } from "react";
import { IMAGES } from "@/lib/images";

// AI 生成的表情包贴纸（脚本生成后自动生效，生成前显示 emoji 占位）
const AI_STICKERS = [
  { url: "/ai-generated/emoji_01_laugh.png",    name: "哈哈大笑",  fallback: "😂" },
  { url: "/ai-generated/emoji_02_clingy.png",   name: "撒娇卖萌",  fallback: "🥺" },
  { url: "/ai-generated/emoji_03_sleep.png",    name: "睡着打盹",  fallback: "😴" },
  { url: "/ai-generated/emoji_04_hungry.png",   name: "超级饿",    fallback: "😋" },
  { url: "/ai-generated/emoji_05_angry.png",    name: "生气了",    fallback: "😤" },
  { url: "/ai-generated/emoji_06_shocked.png",  name: "哇！惊呆了", fallback: "😱" },
  { url: "/ai-generated/emoji_07_love.png",     name: "爱心满满",  fallback: "😍" },
  { url: "/ai-generated/emoji_08_tsundere.png", name: "傲娇翻白眼", fallback: "🙄" },
];

function StickerCard({ s }: { s: typeof AI_STICKERS[0] }) {
  const [failed, setFailed] = useState(false);
  return (
    <motion.div
      style={{
        background: "#FFFFFF",
        borderRadius: 14,
        boxShadow: "4px 4px 12px #D0CCEC, -4px -4px 12px #FFFFFF",
        display: "flex", flexDirection: "column",
        alignItems: "center", overflow: "hidden",
      }}
      whileHover={{ scale: 1.05 }}
    >
      {!failed ? (
        <img
          src={s.url}
          alt={s.name}
          onError={() => setFailed(true)}
          style={{ width: "100%", height: "auto", display: "block" }}
        />
      ) : (
        <div style={{
          aspectRatio: "1", width: "100%",
          display: "flex", flexDirection: "column",
          alignItems: "center", justifyContent: "center", gap: 4,
        }}>
          <span style={{ fontSize: 32 }}>{s.fallback}</span>
          <span style={{ fontSize: 10, color: "#9D99BE" }}>生成中...</span>
        </div>
      )}
      <div style={{ fontSize: 10, color: "#9D99BE", padding: "4px 0 6px", fontWeight: 500 }}>{s.name}</div>
    </motion.div>
  );
}

const PHOTOS = [
  { src: IMAGES.realSmile,  label: "草地笑脸",   hint: "最自然的正面参考" },
  { src: IMAGES.realStick,  label: "叼树枝",     hint: "侧面轮廓" },
  { src: IMAGES.realCar,    label: "车窗兜风",   hint: "45° 侧面" },
  { src: IMAGES.realDesk,   label: "办公室助手", hint: "俯视角度" },
  { src: IMAGES.realBelly,  label: "翻肚皮",     hint: "全身比例" },
  { src: IMAGES.closeup,    label: "脸部特写",   hint: "眼睛、毛色细节" },
];


export default function GallerySection() {
  const { ref, isVisible } = useScrollAnimation(0.08);
  const [lightbox, setLightbox] = useState<number | null>(null);

  return (
    <section id="gallery" style={{ padding: "100px 0", background: "#EAE6F8" }}>
      <div ref={ref} style={{ maxWidth: 1100, margin: "0 auto", padding: "0 24px" }}>

        {/* 标题 */}
        <motion.div
          initial={{ opacity: 0, y: 24 }}
          animate={isVisible ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.7 }}
          style={{ textAlign: "center", marginBottom: 56 }}
        >
          <div style={{
            display: "inline-block", padding: "6px 18px", borderRadius: 20,
            background: "rgba(232,164,192,0.15)", border: "1px solid rgba(232,164,192,0.3)",
            fontSize: 12, fontWeight: 600, color: "#E890B8", marginBottom: 16,
          }}>
            真实案例 · 佳文的照片
          </div>
          <h2 style={{ fontSize: "clamp(26px,4vw,44px)", fontWeight: 800, color: "#3D3660", marginBottom: 12 }}>
            就这几张照片
            <span className="text-gradient-warm">，AI 全搞定</span>
          </h2>
          <p style={{ fontSize: 15, color: "#9D99BE", maxWidth: 420, margin: "0 auto" }}>
            点击照片放大查看 · AI 会从这些角度中提取宠物特征，确保表情包100%像你家的
          </p>
        </motion.div>

        {/* 左右对比布局 */}
        <div style={{ display: "grid", gridTemplateColumns: "1fr auto 1fr", gap: 32, alignItems: "center" }}
          className="grid-cols-1 lg:grid-cols-[1fr_auto_1fr]">

          {/* 左：原始照片 */}
          <motion.div
            initial={{ opacity: 0, x: -30 }}
            animate={isVisible ? { opacity: 1, x: 0 } : {}}
            transition={{ duration: 0.7, delay: 0.1 }}
          >
            <div style={{
              fontSize: 13, fontWeight: 600, color: "#9D99BE",
              marginBottom: 14, display: "flex", alignItems: "center", gap: 6,
            }}>
              📷 主人上传的原始照片（示例）
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 10 }}>
              {PHOTOS.map((p, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={isVisible ? { opacity: 1, scale: 1 } : {}}
                  transition={{ delay: 0.15 + i * 0.07 }}
                  onClick={() => setLightbox(i)}
                  style={{
                    background: "#F0EDF8",
                    borderRadius: 14,
                    boxShadow: "4px 4px 12px #D0CCEC, -4px -4px 12px #FFFFFF",
                    overflow: "hidden", cursor: "pointer",
                    transition: "transform 0.2s",
                  }}
                  whileHover={{ scale: 1.03 }}
                >
                  <img src={p.src} alt={p.label}
                    style={{ width: "100%", aspectRatio: "1", objectFit: "cover", display: "block" }} />
                  <div style={{ padding: "6px 8px" }}>
                    <div style={{ fontSize: 11, fontWeight: 600, color: "#6B6490" }}>{p.label}</div>
                    <div style={{ fontSize: 10, color: "#9D99BE" }}>{p.hint}</div>
                  </div>
                </motion.div>
              ))}
            </div>
          </motion.div>

          {/* 中：箭头 */}
          <motion.div
            initial={{ opacity: 0, scale: 0.5 }}
            animate={isVisible ? { opacity: 1, scale: 1 } : {}}
            transition={{ delay: 0.5 }}
            style={{ textAlign: "center" }}
            className="hidden lg:block"
          >
            <div style={{
              width: 64, height: 64, borderRadius: "50%",
              background: "#F0EDF8",
              boxShadow: "6px 6px 16px #D0CCEC, -6px -6px 16px #FFFFFF",
              display: "flex", alignItems: "center", justifyContent: "center",
              fontSize: 24, margin: "0 auto 8px",
            }}>
              <Sparkles size={26} color="#8B7CC8" />
            </div>
            <div style={{ fontSize: 11, color: "#9D99BE", fontWeight: 600 }}>Gemini AI</div>
          </motion.div>

          {/* 右：生成的表情包 */}
          <motion.div
            initial={{ opacity: 0, x: 30 }}
            animate={isVisible ? { opacity: 1, x: 0 } : {}}
            transition={{ duration: 0.7, delay: 0.2 }}
          >
            <div style={{
              fontSize: 13, fontWeight: 600, color: "#8B7CC8",
              marginBottom: 14, display: "flex", alignItems: "center", gap: 6,
            }}>
              ✨ AI 生成的表情包（8种表情）
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr 1fr", gap: 10 }}>
              {AI_STICKERS.map((s, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, scale: 0.8 }}
                  animate={isVisible ? { opacity: 1, scale: 1 } : {}}
                  transition={{ delay: 0.4 + i * 0.06, type: "spring", stiffness: 200 }}
                >
                  <StickerCard s={s} />
                </motion.div>
              ))}
            </div>
            <div style={{
              marginTop: 14, padding: "10px 16px", borderRadius: 12,
              background: "rgba(139,124,200,0.08)", border: "1px solid rgba(139,124,200,0.15)",
              fontSize: 12, color: "#8B7CC8", textAlign: "center",
            }}>
              以佳文真实照片为参考 · Gemini 3 Pro 生成 · 角色100%一致
            </div>
          </motion.div>
        </div>

        {/* 底部指标 */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={isVisible ? { opacity: 1, y: 0 } : {}}
          transition={{ delay: 0.7 }}
          style={{ display: "grid", gridTemplateColumns: "repeat(3,1fr)", gap: 16, marginTop: 48 }}
          className="grid-cols-1 sm:grid-cols-3"
        >
          {[
            { icon: "📸", title: "5张多角度", desc: "正面·侧面·45°·特写·背面，角度越全越像" },
            { icon: "🤖", title: "Gemini 3 Pro", desc: "Google 最新图像生成模型，角色一致性极高" },
            { icon: "⚡", title: "2-4 分钟出图", desc: "8张表情依次生成，生成完毕自动通知" },
          ].map((item) => (
            <div key={item.title} style={{
              background: "#F0EDF8",
              borderRadius: 16,
              boxShadow: "4px 4px 12px #D0CCEC, -4px -4px 12px #FFFFFF",
              padding: "20px 22px",
              display: "flex", gap: 14, alignItems: "flex-start",
            }}>
              <span style={{ fontSize: 24 }}>{item.icon}</span>
              <div>
                <div style={{ fontSize: 14, fontWeight: 700, color: "#3D3660", marginBottom: 4 }}>{item.title}</div>
                <div style={{ fontSize: 12, color: "#9D99BE", lineHeight: 1.5 }}>{item.desc}</div>
              </div>
            </div>
          ))}
        </motion.div>
      </div>

      {/* Lightbox */}
      <AnimatePresence>
        {lightbox !== null && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setLightbox(null)}
            style={{
              position: "fixed", inset: 0, zIndex: 50,
              display: "flex", alignItems: "center", justifyContent: "center",
              background: "rgba(61,54,96,0.6)", backdropFilter: "blur(8px)", padding: 20,
            }}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              onClick={(e) => e.stopPropagation()}
              style={{
                background: "#F0EDF8",
                borderRadius: 24,
                boxShadow: "16px 16px 40px #D0CCEC, -16px -16px 40px #FFFFFF",
                overflow: "hidden", maxWidth: 480, width: "100%",
              }}
            >
              <img src={PHOTOS[lightbox].src} alt={PHOTOS[lightbox].label}
                style={{ width: "100%", display: "block" }} />
              <div style={{ padding: "14px 20px", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <div>
                  <div style={{ fontSize: 15, fontWeight: 700, color: "#3D3660" }}>{PHOTOS[lightbox].label}</div>
                  <div style={{ fontSize: 12, color: "#9D99BE" }}>{PHOTOS[lightbox].hint}</div>
                </div>
                <button onClick={() => setLightbox(null)} style={{
                  background: "none", border: "none", cursor: "pointer",
                  color: "#9D99BE", padding: 4,
                }}>
                  <X size={18} />
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </section>
  );
}
