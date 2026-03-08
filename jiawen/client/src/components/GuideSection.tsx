// Design: Mental Health App · 拍摄指南 · 5个角度
import { motion } from "framer-motion";
import { useScrollAnimation } from "@/hooks/useScrollAnimation";
import { IMAGES } from "@/lib/images";
import { CheckCircle2, AlertCircle, Lightbulb } from "lucide-react";
import { Link } from "wouter";

const ANGLES = [
  {
    num: "1",
    icon: "🐾",
    title: "正面站立",
    desc: "宠物面向镜头，全身入画，脸部清晰",
    tips: ["光线从前方照来，避免逆光", "宠物站立或坐姿均可", "与宠物保持1-2米距离"],
    preview: IMAGES.realSmile,
    color: "#8B7CC8",
    must: true,
  },
  {
    num: "2",
    icon: "◀",
    title: "左侧面",
    desc: "身体完全侧对镜头，体型轮廓最清晰",
    tips: ["从左侧拍摄，捕捉完整体型", "尾巴入画效果更好"],
    preview: IMAGES.realStick,
    color: "#E890B8",
    must: true,
  },
  {
    num: "3",
    icon: "↙",
    title: "右 45° 斜前方",
    desc: "黄金角度，展示立体感和深度",
    tips: ["站在宠物右前方约45°", "这个角度表情包立体感最强"],
    preview: IMAGES.realCar,
    color: "#6AABCC",
    must: false,
  },
  {
    num: "4",
    icon: "🔍",
    title: "脸部特写",
    desc: "靠近拍眼睛、耳朵、鼻子，记录毛色细节",
    tips: ["对焦在眼睛上", "毛色和斑纹越清晰越好", "自然光下拍摄最佳"],
    preview: IMAGES.realDesk,
    color: "#F5A55A",
    must: false,
  },
  {
    num: "5",
    icon: "▶",
    title: "背面",
    desc: "背部和尾巴的纹理，补充AI对宠物的认识",
    tips: ["让宠物自然站立或走路", "尾巴的形状很重要"],
    preview: IMAGES.realBelly,
    color: "#7BC8A4",
    must: false,
  },
];

export default function GuideSection() {
  const { ref, isVisible } = useScrollAnimation(0.06);

  return (
    <section id="guide" style={{ padding: "100px 0", background: "#EAE6F8" }}>
      <div ref={ref} style={{ maxWidth: 1000, margin: "0 auto", padding: "0 24px" }}>

        {/* 标题 */}
        <motion.div
          initial={{ opacity: 0, y: 24 }}
          animate={isVisible ? { opacity: 1, y: 0 } : {}}
          style={{ textAlign: "center", marginBottom: 60 }}
        >
          <div style={{
            display: "inline-block", padding: "6px 18px", borderRadius: 20,
            background: "rgba(245,165,90,0.12)", border: "1px solid rgba(245,165,90,0.25)",
            fontSize: 12, fontWeight: 600, color: "#F5A55A", marginBottom: 16,
          }}>
            拍摄小指南
          </div>
          <h2 style={{ fontSize: "clamp(26px,4vw,44px)", fontWeight: 800, color: "#3D3660", marginBottom: 12 }}>
            怎么拍，效果最好？
          </h2>
          <p style={{ fontSize: 15, color: "#9D99BE", maxWidth: 440, margin: "0 auto" }}>
            5个角度各拍一张，AI就能准确还原你家宝贝的样子。<br />
            前2张是必须的，后3张可选但能显著提升效果
          </p>
        </motion.div>

        {/* 5个角度 */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(5,1fr)", gap: 16 }}
          className="grid-cols-1 sm:grid-cols-2 lg:grid-cols-5">
          {ANGLES.map((angle, i) => (
            <motion.div
              key={angle.num}
              initial={{ opacity: 0, y: 28 }}
              animate={isVisible ? { opacity: 1, y: 0 } : {}}
              transition={{ duration: 0.55, delay: 0.1 + i * 0.1 }}
              style={{
                background: "#F0EDF8",
                borderRadius: 18,
                boxShadow: "6px 6px 16px #D0CCEC, -6px -6px 16px #FFFFFF",
                overflow: "hidden",
              }}
            >
              {/* 预览图 */}
              <div style={{ position: "relative" }}>
                <img src={angle.preview} alt={angle.title}
                  style={{ width: "100%", aspectRatio: "1", objectFit: "cover", display: "block" }} />
                {/* 必须/可选标签 */}
                <div style={{
                  position: "absolute", top: 8, left: 8,
                  background: angle.must ? angle.color : "rgba(240,237,248,0.9)",
                  color: angle.must ? "#fff" : "#9D99BE",
                  borderRadius: 8, padding: "3px 8px",
                  fontSize: 10, fontWeight: 700,
                }}>
                  {angle.must ? "必须" : "推荐"}
                </div>
                {/* 步骤圆圈 */}
                <div style={{
                  position: "absolute", top: 8, right: 8,
                  width: 26, height: 26, borderRadius: "50%",
                  background: angle.color,
                  display: "flex", alignItems: "center", justifyContent: "center",
                  fontSize: 11, fontWeight: 800, color: "#fff",
                }}>
                  {angle.num}
                </div>
              </div>

              {/* 文字 */}
              <div style={{ padding: "14px 14px 16px" }}>
                <div style={{ fontSize: 14, fontWeight: 700, color: "#3D3660", marginBottom: 4 }}>
                  {angle.icon} {angle.title}
                </div>
                <p style={{ fontSize: 11, color: "#9D99BE", lineHeight: 1.5, marginBottom: 10 }}>
                  {angle.desc}
                </p>
                <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
                  {angle.tips.map((tip, ti) => (
                    <div key={ti} style={{ display: "flex", alignItems: "flex-start", gap: 6 }}>
                      <CheckCircle2 size={11} color={angle.color} style={{ flexShrink: 0, marginTop: 1 }} />
                      <span style={{ fontSize: 11, color: "#9D99BE", lineHeight: 1.4 }}>{tip}</span>
                    </div>
                  ))}
                </div>
              </div>
            </motion.div>
          ))}
        </div>

        {/* 温馨提示 */}
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={isVisible ? { opacity: 1, y: 0 } : {}}
          transition={{ delay: 0.7 }}
          style={{
            marginTop: 36, padding: "18px 24px", borderRadius: 16,
            background: "#F0EDF8",
            boxShadow: "4px 4px 12px #D0CCEC, -4px -4px 12px #FFFFFF",
            display: "flex", gap: 14, alignItems: "flex-start",
          }}
        >
          <Lightbulb size={18} color="#F5A55A" style={{ flexShrink: 0, marginTop: 2 }} />
          <div>
            <div style={{ fontSize: 13, fontWeight: 700, color: "#3D3660", marginBottom: 6 }}>拍摄小贴士</div>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(3,1fr)", gap: "6px 24px" }}
              className="grid-cols-1 sm:grid-cols-3">
              {[
                "自然光或室内充足光线，避免闪光灯",
                "宠物清醒状态下拍摄，避免运动模糊",
                "背景简洁效果更好，但不强求",
              ].map((tip, i) => (
                <div key={i} style={{ display: "flex", alignItems: "flex-start", gap: 6 }}>
                  <AlertCircle size={12} color="#F5A55A" style={{ flexShrink: 0, marginTop: 1 }} />
                  <span style={{ fontSize: 12, color: "#9D99BE", lineHeight: 1.5 }}>{tip}</span>
                </div>
              ))}
            </div>
          </div>
        </motion.div>

        {/* CTA */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={isVisible ? { opacity: 1 } : {}}
          transition={{ delay: 0.8 }}
          style={{ textAlign: "center", marginTop: 48 }}
        >
          <Link href="/demo">
            <span style={{
              display: "inline-flex", alignItems: "center", gap: 8,
              padding: "13px 36px", borderRadius: 14,
              background: "linear-gradient(135deg, #8B7CC8, #E8A4C0)",
              color: "#fff", fontSize: 14, fontWeight: 700,
              cursor: "pointer", textDecoration: "none",
              boxShadow: "0 6px 24px rgba(139,124,200,0.35)",
            }}>
              📷 我准备好了，开始生成
            </span>
          </Link>
          <div style={{ fontSize: 12, color: "#9D99BE", marginTop: 10 }}>
            就算只有1张照片，也可以先试试看
          </div>
        </motion.div>
      </div>
    </section>
  );
}
