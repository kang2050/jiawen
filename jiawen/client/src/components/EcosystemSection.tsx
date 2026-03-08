// Design: Mental Health App · 如何使用 · 3步完成
import { motion } from "framer-motion";
import { useScrollAnimation } from "@/hooks/useScrollAnimation";
import { Link } from "wouter";
import { ArrowRight } from "lucide-react";

const STEPS = [
  {
    num: "01",
    emoji: "🎨",
    title: "选择你喜欢的风格",
    desc: "皮克斯3D、日系软萌、水彩手绘、国潮插画——4种风格，找到最符合宝贝气质的那一款",
    color: "#8B7CC8",
    bg: "#F0EDF8",
    tags: ["点击选择", "预览对比", "随时换"],
  },
  {
    num: "02",
    emoji: "📷",
    title: "上传5张不同角度的照片",
    desc: "正面站立、左侧面、右45°、脸部特写、背面。照片越多样，AI越了解你的宝贝",
    color: "#E890B8",
    bg: "#FFF0F6",
    tags: ["5个角度", "支持JPG/PNG", "拍摄指南在下方"],
  },
  {
    num: "03",
    emoji: "✨",
    title: "等2-4分钟，下载8张贴纸",
    desc: "AI自动决定8种表情（哈哈大笑、撒娇、睡觉、生气…），生成完成后下载PNG，随手分享",
    color: "#6AABCC",
    bg: "#EFF8FF",
    tags: ["8种表情", "PNG格式", "一键下载全部"],
  },
];

export default function EcosystemSection() {
  const { ref, isVisible } = useScrollAnimation(0.08);

  return (
    <section id="how" style={{ padding: "100px 0", background: "#F5F2FF" }}>
      <div ref={ref} style={{ maxWidth: 1100, margin: "0 auto", padding: "0 24px" }}>

        {/* 标题 */}
        <motion.div
          initial={{ opacity: 0, y: 24 }}
          animate={isVisible ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.7 }}
          style={{ textAlign: "center", marginBottom: 64 }}
        >
          <div style={{
            display: "inline-block", padding: "6px 18px", borderRadius: 20,
            background: "rgba(106,171,204,0.12)", border: "1px solid rgba(106,171,204,0.25)",
            fontSize: 12, fontWeight: 600, color: "#6AABCC", marginBottom: 16,
          }}>
            操作超简单
          </div>
          <h2 style={{ fontSize: "clamp(26px,4vw,44px)", fontWeight: 800, color: "#3D3660", marginBottom: 12 }}>
            3步完成，
            <span className="text-gradient-teal">无需任何技术</span>
          </h2>
          <p style={{ fontSize: 15, color: "#9D99BE", maxWidth: 420, margin: "0 auto" }}>
            从选风格到拿到表情包，整个流程不超过5分钟
          </p>
        </motion.div>

        {/* 3步卡片 */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(3,1fr)", gap: 24, position: "relative" }}
          className="grid-cols-1 sm:grid-cols-3">

          {/* 连接线（桌面端） */}
          <div style={{
            position: "absolute", top: 56, left: "calc(33.3% - 12px)", right: "calc(33.3% - 12px)",
            height: 2,
            background: "linear-gradient(90deg, #8B7CC8, #E890B8, #6AABCC)",
            borderRadius: 2, zIndex: 0,
          }} className="hidden sm:block" />

          {STEPS.map((step, i) => (
            <motion.div
              key={step.num}
              initial={{ opacity: 0, y: 32 }}
              animate={isVisible ? { opacity: 1, y: 0 } : {}}
              transition={{ duration: 0.6, delay: 0.1 + i * 0.15 }}
              style={{ position: "relative", zIndex: 1 }}
            >
              {/* 步骤圆圈 */}
              <div style={{
                width: 56, height: 56, borderRadius: "50%",
                background: "#F0EDF8",
                boxShadow: `6px 6px 16px #D0CCEC, -6px -6px 16px #FFFFFF, 0 0 0 3px ${step.color}40`,
                display: "flex", alignItems: "center", justifyContent: "center",
                margin: "0 auto 24px",
                fontSize: 22,
              }}>
                {step.emoji}
              </div>

              {/* 卡片 */}
              <div style={{
                background: "#F0EDF8",
                borderRadius: 20,
                boxShadow: "8px 8px 20px #D0CCEC, -8px -8px 20px #FFFFFF",
                padding: "24px 22px",
              }}>
                <div style={{
                  fontSize: 11, fontWeight: 700, color: step.color,
                  marginBottom: 8, letterSpacing: "0.05em",
                }}>
                  STEP {step.num}
                </div>
                <h3 style={{ fontSize: 16, fontWeight: 700, color: "#3D3660", marginBottom: 10, lineHeight: 1.4 }}>
                  {step.title}
                </h3>
                <p style={{ fontSize: 13, color: "#9D99BE", lineHeight: 1.65, marginBottom: 16 }}>
                  {step.desc}
                </p>
                <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
                  {step.tags.map((tag) => (
                    <span key={tag} style={{
                      padding: "4px 10px", borderRadius: 10, fontSize: 11,
                      background: step.bg, color: step.color, fontWeight: 600,
                      border: `1px solid ${step.color}25`,
                    }}>{tag}</span>
                  ))}
                </div>
              </div>
            </motion.div>
          ))}
        </div>

        {/* CTA */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={isVisible ? { opacity: 1, y: 0 } : {}}
          transition={{ delay: 0.65 }}
          style={{ textAlign: "center", marginTop: 56 }}
        >
          <Link href="/demo">
            <span style={{
              display: "inline-flex", alignItems: "center", gap: 8,
              padding: "14px 40px", borderRadius: 14,
              background: "linear-gradient(135deg, #8B7CC8, #E8A4C0)",
              color: "#fff", fontSize: 15, fontWeight: 700,
              cursor: "pointer", textDecoration: "none",
              boxShadow: "0 8px 28px rgba(139,124,200,0.4)",
            }}>
              现在就试一试 <ArrowRight size={16} />
            </span>
          </Link>
        </motion.div>
      </div>
    </section>
  );
}
