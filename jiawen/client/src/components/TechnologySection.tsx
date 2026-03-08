// Design: Mental Health App · 4种风格展示
import { motion } from "framer-motion";
import { useScrollAnimation } from "@/hooks/useScrollAnimation";
import { IMAGES } from "@/lib/images";
import { useState } from "react";

const STYLES = [
  {
    id: "pixar",
    emoji: "🎬",
    name: "皮克斯 3D",
    desc: "圆润立体，毛绒质感，像迪士尼电影里的动物角色",
    accent: "#F5A55A",
    accentBg: "#FFF5EB",
    preview: "/ai-generated/style_pixar.png",
    fallback: IMAGES.model3dFront,
    tags: ["3D 立体感", "软萌毛发", "温暖色调"],
    best: "适合卖萌、撒娇类表情",
  },
  {
    id: "japanese",
    emoji: "🌸",
    name: "日系软萌",
    desc: "LINE 贴纸风，厚线条扁平，粉嫩系配色",
    accent: "#E890B8",
    accentBg: "#FFF0F6",
    preview: "/ai-generated/style_japanese.png",
    fallback: IMAGES.model3dSide,
    tags: ["厚线条", "扁平设计", "少女粉"],
    best: "适合微信表情、微博贴纸",
  },
  {
    id: "ghibli",
    emoji: "🌿",
    name: "吉卜力动画",
    desc: "宫崎骏手绘风，温暖细腻，像森林里的精灵伙伴",
    accent: "#5BA86E",
    accentBg: "#F0FBF3",
    preview: "/ai-generated/style_ghibli.png",
    fallback: IMAGES.model3dQuarter,
    tags: ["宫崎骏风", "手绘动画", "温暖治愈"],
    best: "适合治愈系、情感类内容",
  },
  {
    id: "guochao",
    emoji: "🏮",
    name: "国潮着装",
    desc: "给宝贝穿上国潮服饰，汉服马甲、云纹刺绣，潮爆全场",
    accent: "#E05D45",
    accentBg: "#FFF2EF",
    preview: "/ai-generated/style_guochao.png",
    fallback: IMAGES.model3dBack,
    tags: ["国潮服饰", "汉服刺绣", "潮牌造型"],
    best: "适合节日、节点营销",
  },
];

function StyleImage({ s }: { s: typeof STYLES[0] }) {
  const [src, setSrc] = useState(s.preview);
  return (
    <div style={{
      background: s.accentBg, position: "relative",
      display: "flex", alignItems: "center", justifyContent: "center",
      padding: 12,
    }}>
      <img
        src={src}
        alt={s.name}
        onError={() => setSrc(s.fallback)}
        style={{ width: "100%", height: "auto", display: "block", borderRadius: 8 }}
      />
      <div style={{
        position: "absolute", top: 18, left: 18,
        background: "rgba(255,255,255,0.92)", borderRadius: 8,
        padding: "3px 10px", fontSize: 11, fontWeight: 700, color: s.accent,
        border: `1px solid ${s.accent}33`,
        backdropFilter: "blur(8px)",
      }}>
        {s.emoji} {s.name}
      </div>
    </div>
  );
}

export default function TechnologySection() {
  const { ref, isVisible } = useScrollAnimation(0.08);

  return (
    <section id="styles" style={{ padding: "100px 0", background: "#F5F2FF" }}>
      <div ref={ref} style={{ maxWidth: 1200, margin: "0 auto", padding: "0 24px" }}>

        {/* 标题 */}
        <motion.div
          initial={{ opacity: 0, y: 24 }}
          animate={isVisible ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.7 }}
          style={{ textAlign: "center", marginBottom: 64 }}
        >
          <div style={{
            display: "inline-block", padding: "6px 18px", borderRadius: 20,
            background: "rgba(139,124,200,0.1)", border: "1px solid rgba(139,124,200,0.2)",
            fontSize: 12, fontWeight: 600, color: "#8B7CC8", marginBottom: 16,
          }}>
            4 种风格任你选
          </div>
          <h2 style={{ fontSize: "clamp(28px,4vw,46px)", fontWeight: 800, color: "#3D3660", marginBottom: 12 }}>
            选一种最像你家宝贝的气质
          </h2>
          <p style={{ fontSize: 16, color: "#9D99BE", maxWidth: 480, margin: "0 auto" }}>
            风格由你定，表情由 AI 定。同一套照片可以生成不同风格，随时切换
          </p>
        </motion.div>

        {/* 4张风格卡片 */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(4,1fr)", gap: 20 }} className="grid-cols-1 sm:grid-cols-2 lg:grid-cols-4">
          {STYLES.map((s, i) => (
            <motion.div
              key={s.id}
              initial={{ opacity: 0, y: 32 }}
              animate={isVisible ? { opacity: 1, y: 0 } : {}}
              transition={{ duration: 0.6, delay: 0.12 + i * 0.12 }}
              style={{
                background: "#F0EDF8",
                borderRadius: 20,
                boxShadow: "8px 8px 20px #D0CCEC, -8px -8px 20px #FFFFFF",
                overflow: "hidden",
              }}
            >
              {/* 图片区（AI生成图，失败时用 fallback） */}
              <StyleImage s={s} />

              {/* 文字区 */}
              <div style={{ padding: "18px 20px 20px" }}>
                <p style={{ fontSize: 13, color: "#6B6490", lineHeight: 1.6, marginBottom: 14 }}>{s.desc}</p>
                <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginBottom: 12 }}>
                  {s.tags.map((tag) => (
                    <span key={tag} style={{
                      padding: "3px 10px", borderRadius: 10, fontSize: 11,
                      background: s.accentBg, color: s.accent, fontWeight: 600,
                    }}>{tag}</span>
                  ))}
                </div>
                <div style={{ fontSize: 11, color: "#9D99BE", fontStyle: "italic" }}>💡 {s.best}</div>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
