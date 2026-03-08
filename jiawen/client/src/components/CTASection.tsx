// Design: Mental Health App · 行动号召
import { motion } from "framer-motion";
import { useScrollAnimation } from "@/hooks/useScrollAnimation";
import { IMAGES } from "@/lib/images";
import { Sparkles, ArrowRight, Heart } from "lucide-react";
import { Link } from "wouter";

export default function CTASection() {
  const { ref, isVisible } = useScrollAnimation(0.15);

  return (
    <section style={{ padding: "100px 0", background: "#EAE6F8" }}>
      <div ref={ref} style={{ maxWidth: 800, margin: "0 auto", padding: "0 24px", textAlign: "center" }}>
        <motion.div
          initial={{ opacity: 0, y: 28 }}
          animate={isVisible ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.8 }}
        >
          {/* 大图 */}
          <div style={{
            background: "#F0EDF8",
            borderRadius: 28,
            boxShadow: "12px 12px 32px #D0CCEC, -12px -12px 32px #FFFFFF",
            overflow: "hidden", marginBottom: 48, padding: 8,
          }}>
            <div style={{ position: "relative", borderRadius: 22, overflow: "hidden" }}>
              <img
                src={IMAGES.pawsmemeDemo}
                alt="表情包演示"
                style={{ width: "100%", display: "block", maxHeight: 340, objectFit: "cover" }}
              />
              <div style={{
                position: "absolute", inset: 0,
                background: "linear-gradient(to top, rgba(61,54,96,0.7) 0%, transparent 60%)",
              }} />
              <div style={{ position: "absolute", bottom: 24, left: 0, right: 0, textAlign: "center" }}>
                <div style={{ fontSize: 28, fontWeight: 800, color: "#fff" }}>把宠物变成表情包</div>
                <div style={{ fontSize: 15, color: "rgba(255,255,255,0.75)", marginTop: 6 }}>让宝贝的可爱陪你每次聊天</div>
              </div>
            </div>
          </div>

          {/* 文案 */}
          <div style={{
            display: "inline-flex", alignItems: "center", gap: 6,
            padding: "6px 16px", borderRadius: 20, marginBottom: 20,
            background: "rgba(139,124,200,0.1)", border: "1px solid rgba(139,124,200,0.2)",
          }}>
            <Sparkles size={13} color="#8B7CC8" />
            <span style={{ fontSize: 12, fontWeight: 600, color: "#8B7CC8" }}>现在就开始</span>
          </div>

          <h2 style={{ fontSize: "clamp(28px,5vw,52px)", fontWeight: 800, color: "#3D3660", marginBottom: 16, lineHeight: 1.2 }}>
            你家宝贝也值得
            <br />
            <span className="text-gradient-purple">专属表情包</span>
          </h2>

          <p style={{ fontSize: 16, color: "#9D99BE", lineHeight: 1.7, maxWidth: 480, margin: "0 auto 40px" }}>
            上传5张照片，选一种风格，2-4分钟后拿到8张专属贴纸。
            再也不用羡慕别人家的宠物了。
          </p>

          <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 16 }}>
            <Link href="/demo">
              <span style={{
                display: "inline-flex", alignItems: "center", gap: 8,
                padding: "16px 48px", borderRadius: 16,
                background: "linear-gradient(135deg, #8B7CC8, #E8A4C0)",
                color: "#fff", fontSize: 16, fontWeight: 800,
                cursor: "pointer", textDecoration: "none",
                boxShadow: "0 10px 32px rgba(139,124,200,0.45)",
              }}>
                <Heart size={18} />
                现在就帮宝贝做表情包
                <ArrowRight size={18} />
              </span>
            </Link>

            <div style={{ fontSize: 13, color: "#9D99BE" }}>无需注册 · 直接使用 · 免费试用</div>
          </div>

          {/* 信任标签 */}
          <div style={{
            display: "flex", flexWrap: "wrap", alignItems: "center",
            justifyContent: "center", gap: 20, marginTop: 40,
            paddingTop: 32, borderTop: "1px solid #DDD8F0",
          }}>
            {["Gemini 3 Pro Image Preview", "4种画风", "8种表情", "PNG可下载分享"].map((tag) => (
              <div key={tag} style={{ display: "flex", alignItems: "center", gap: 6 }}>
                <div style={{ width: 6, height: 6, borderRadius: "50%", background: "#B8AEE0" }} />
                <span style={{ fontSize: 12, color: "#9D99BE" }}>{tag}</span>
              </div>
            ))}
          </div>
        </motion.div>
      </div>
    </section>
  );
}
