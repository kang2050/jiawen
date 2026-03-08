// Design: Mental Health App · Neumorphism · Calm Pastel
// Hero: 宠物表情包生成 主视觉
import { motion } from "framer-motion";
import { Sparkles, ArrowRight, Heart } from "lucide-react";
import { IMAGES } from "@/lib/images";
import { Link } from "wouter";

const STYLE_PILLS = [
  { label: "皮克斯 3D",  color: "#F5A55A", bg: "#FFF5EB" },
  { label: "日系软萌",   color: "#E890B8", bg: "#FFF0F6" },
  { label: "水彩手绘",   color: "#6AABCC", bg: "#EFF8FF" },
  { label: "国潮插画",   color: "#E05D45", bg: "#FFF2EF" },
];

const STICKER_EMOJIS = ["😂", "🥺", "😴", "😋", "😤", "😱", "😍", "🙄"];

export default function HeroSection() {
  return (
    <section id="hero" style={{
      minHeight: "100vh",
      background: "linear-gradient(160deg, #F5F2FF 0%, #FEF0F7 50%, #F0F5FF 100%)",
      display: "flex", alignItems: "center",
      overflow: "hidden", position: "relative",
      paddingTop: 64,
    }}>

      {/* 背景浮动圆 */}
      {[
        { w: 400, h: 400, top: "-10%", left: "-5%", color: "rgba(139,124,200,0.06)" },
        { w: 300, h: 300, top: "60%",  right: "-8%", color: "rgba(232,164,192,0.07)" },
        { w: 200, h: 200, top: "30%",  left: "40%",  color: "rgba(106,171,204,0.05)" },
      ].map((b, i) => (
        <div key={i} style={{
          position: "absolute", width: b.w, height: b.h, borderRadius: "50%",
          background: b.color, top: b.top, left: b.left, right: b.right,
          filter: "blur(60px)", pointerEvents: "none",
        }} />
      ))}

      <div style={{ maxWidth: 1200, margin: "0 auto", padding: "40px 24px 60px", width: "100%", position: "relative" }}>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 48, alignItems: "center" }}
          className="grid-cols-1 lg:grid-cols-2">

          {/* Left */}
          <motion.div initial={{ opacity: 0, x: -40 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.8, delay: 0.1 }}>

            <div style={{
              display: "inline-flex", alignItems: "center", gap: 6,
              padding: "6px 14px", borderRadius: 20, marginBottom: 20,
              background: "rgba(139,124,200,0.1)", border: "1px solid rgba(139,124,200,0.2)",
            }}>
              <Sparkles size={13} color="#8B7CC8" />
              <span style={{ fontSize: 12, fontWeight: 600, color: "#8B7CC8" }}>AI 宠物表情包生成</span>
            </div>

            <h1 style={{
              fontSize: "clamp(32px, 5vw, 58px)",
              fontWeight: 800, lineHeight: 1.15,
              color: "#3D3660", marginBottom: 16,
            }}>
              把毛孩子变成
              <br />
              <span className="text-gradient-purple">表情包明星</span>
            </h1>

            <p style={{
              fontSize: 17, color: "#9D99BE", lineHeight: 1.7,
              maxWidth: 440, marginBottom: 28,
            }}>
              上传5张照片，选一种喜欢的风格，<br />
              AI 帮你生成 <strong style={{ color: "#8B7CC8" }}>8张专属表情包</strong>，2-4分钟搞定
            </p>

            {/* Style pills */}
            <div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginBottom: 32 }}>
              {STYLE_PILLS.map((s) => (
                <span key={s.label} style={{
                  padding: "5px 14px", borderRadius: 20,
                  background: s.bg, color: s.color,
                  fontSize: 12, fontWeight: 600,
                  border: `1px solid ${s.color}33`,
                }}>
                  {s.label}
                </span>
              ))}
            </div>

            {/* CTAs */}
            <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
              <Link href="/demo">
                <span style={{
                  display: "inline-flex", alignItems: "center", gap: 8,
                  padding: "14px 32px", borderRadius: 14,
                  background: "linear-gradient(135deg, #8B7CC8, #E8A4C0)",
                  color: "#fff", fontSize: 15, fontWeight: 700, cursor: "pointer",
                  textDecoration: "none",
                  boxShadow: "0 8px 28px rgba(139,124,200,0.4)",
                }}>
                  <Sparkles size={17} />
                  立即生成
                  <ArrowRight size={16} />
                </span>
              </Link>
              <button onClick={() => document.querySelector("#gallery")?.scrollIntoView({ behavior: "smooth" })}
                style={{
                  display: "inline-flex", alignItems: "center", gap: 6,
                  padding: "14px 24px", borderRadius: 14,
                  background: "#F0EDF8",
                  boxShadow: "4px 4px 12px #D0CCEC, -4px -4px 12px #FFFFFF",
                  border: "none", cursor: "pointer",
                  fontSize: 15, fontWeight: 600, color: "#6B6490",
                }}>
                <Heart size={16} color="#E8A4C0" />
                看效果样片
              </button>
            </div>

            {/* 数字 */}
            <div style={{
              display: "flex", gap: 32, marginTop: 40, paddingTop: 32,
              borderTop: "1px solid #EAE6F8",
            }}>
              {[
                { v: "8张", l: "表情包" },
                { v: "4种", l: "风格选择" },
                { v: "5张", l: "照片即可" },
              ].map((d) => (
                <div key={d.l}>
                  <div style={{ fontSize: 26, fontWeight: 800 }} className="text-gradient-purple">{d.v}</div>
                  <div style={{ fontSize: 12, color: "#9D99BE", marginTop: 2 }}>{d.l}</div>
                </div>
              ))}
            </div>
          </motion.div>

          {/* Right: 照片 + 浮动贴纸效果 */}
          <motion.div
            initial={{ opacity: 0, scale: 0.92 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.9, delay: 0.3 }}
            style={{ position: "relative" }}
          >
            {/* 主图 neumorphic 框 */}
            <div style={{
              background: "#F0EDF8",
              borderRadius: 28,
              boxShadow: "12px 12px 32px #D0CCEC, -12px -12px 32px #FFFFFF",
              padding: 8, position: "relative",
            }}>
              <img
                src={IMAGES.realSmile}
                alt="佳文"
                style={{ width: "100%", borderRadius: 22, display: "block", objectFit: "cover", maxHeight: 420 }}
              />
              {/* 品牌角标 */}
              <div style={{
                position: "absolute", bottom: 20, left: 20,
                background: "rgba(240,237,248,0.9)", backdropFilter: "blur(12px)",
                borderRadius: 12, padding: "8px 14px",
                boxShadow: "0 4px 16px rgba(139,124,200,0.2)",
              }}>
                <div style={{ fontSize: 11, color: "#8B7CC8", fontWeight: 600 }}>✨ AI 已识别</div>
                <div style={{ fontSize: 14, fontWeight: 700, color: "#3D3660" }}>边牧 · 佳文</div>
              </div>
            </div>

            {/* 浮动表情包 */}
            {STICKER_EMOJIS.map((emoji, i) => {
              const angle = (i / STICKER_EMOJIS.length) * 360;
              const r = 52;
              const x = 50 + r * Math.cos((angle * Math.PI) / 180);
              const y = 50 + r * Math.sin((angle * Math.PI) / 180);
              return (
                <motion.div
                  key={i}
                  animate={{ y: [0, i % 2 === 0 ? -8 : 8, 0] }}
                  transition={{ duration: 2 + i * 0.3, repeat: Infinity, ease: "easeInOut" }}
                  style={{
                    position: "absolute",
                    left: `${x}%`, top: `${y}%`,
                    transform: "translate(-50%,-50%)",
                    width: 44, height: 44, borderRadius: 12,
                    background: "#F0EDF8",
                    boxShadow: "4px 4px 10px #D0CCEC, -4px -4px 10px #FFFFFF",
                    display: "flex", alignItems: "center", justifyContent: "center",
                    fontSize: 22,
                    opacity: 0.75,
                  }}
                >
                  {emoji}
                </motion.div>
              );
            })}

            {/* 右上浮动卡片 */}
            <motion.div
              animate={{ y: [-6, 6, -6] }}
              transition={{ duration: 4, repeat: Infinity }}
              style={{
                position: "absolute", top: -16, right: -16,
                background: "#F0EDF8",
                boxShadow: "6px 6px 16px #D0CCEC, -6px -6px 16px #FFFFFF",
                borderRadius: 16, padding: "12px 18px",
              }}
            >
              <div style={{ fontSize: 11, color: "#9D99BE", fontWeight: 600 }}>生成耗时</div>
              <div style={{ fontSize: 18, fontWeight: 800, color: "#8B7CC8" }}>2-4 分钟</div>
            </motion.div>
          </motion.div>
        </div>
      </div>

      {/* 向下滚动提示 */}
      <motion.div
        initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 1.5 }}
        style={{ position: "absolute", bottom: 28, left: "50%", transform: "translateX(-50%)", textAlign: "center" }}
      >
        <motion.div animate={{ y: [0, 8, 0] }} transition={{ duration: 1.5, repeat: Infinity }}>
          <div style={{ width: 2, height: 40, background: "linear-gradient(#8B7CC8, transparent)", margin: "0 auto", borderRadius: 2 }} />
        </motion.div>
      </motion.div>
    </section>
  );
}
