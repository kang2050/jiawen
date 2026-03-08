// Design: Mental Health App · 数字指标横幅
import { motion } from "framer-motion";
import { useScrollAnimation } from "@/hooks/useScrollAnimation";

const STATS = [
  { value: "4",      unit: "种风格",   desc: "皮克斯·日系·水彩·国潮" },
  { value: "8",      unit: "张表情包", desc: "每次生成，AI 自主决定表情" },
  { value: "5",      unit: "张照片",   desc: "最少1张，5张效果最佳" },
  { value: "2-4",    unit: "分钟",     desc: "从上传到拿到成品" },
  { value: "100%",   unit: "专属定制", desc: "基于你宠物的真实形象" },
  { value: "∞",      unit: "分享次数", desc: "PNG格式，随意分享" },
];

export default function SpecsSection() {
  const { ref, isVisible } = useScrollAnimation(0.2);

  return (
    <section style={{ padding: "60px 0", background: "#EAE6F8", borderTop: "1px solid #DDD8F0", borderBottom: "1px solid #DDD8F0" }}>
      <div ref={ref} style={{ maxWidth: 1200, margin: "0 auto", padding: "0 24px" }}>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(6,1fr)", gap: 24 }} className="grid-cols-2 sm:grid-cols-3 lg:grid-cols-6">
          {STATS.map((stat, i) => (
            <motion.div
              key={stat.unit}
              initial={{ opacity: 0, y: 20 }}
              animate={isVisible ? { opacity: 1, y: 0 } : {}}
              transition={{ duration: 0.5, delay: i * 0.08 }}
              style={{ textAlign: "center" }}
            >
              <div style={{ fontSize: "clamp(22px,3vw,32px)", fontWeight: 800 }} className="text-gradient-purple">
                {stat.value}
              </div>
              <div style={{ fontSize: 13, fontWeight: 700, color: "#8B7CC8", marginTop: 2 }}>{stat.unit}</div>
              <div style={{ fontSize: 11, color: "#9D99BE", marginTop: 4, lineHeight: 1.4 }}>{stat.desc}</div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
