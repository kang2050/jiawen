// Design: Mental Health App · Footer
import { Heart, Mail } from "lucide-react";

export default function Footer() {
  const go = (href: string) => document.querySelector(href)?.scrollIntoView({ behavior: "smooth" });

  return (
    <footer style={{
      background: "#F0EDF8",
      borderTop: "1px solid #DDD8F0",
    }}>
      <div style={{ maxWidth: 1100, margin: "0 auto", padding: "56px 24px 40px" }}>
        <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr 1fr 1fr", gap: 48, marginBottom: 48 }}
          className="grid-cols-1 sm:grid-cols-2 lg:grid-cols-4">

          {/* 品牌 */}
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 14 }}>
              <div style={{
                width: 36, height: 36, borderRadius: 10,
                background: "linear-gradient(135deg, #8B7CC8, #E8A4C0)",
                display: "flex", alignItems: "center", justifyContent: "center",
                boxShadow: "0 4px 12px rgba(139,124,200,0.35)",
              }}>
                <span style={{ fontSize: 14, fontWeight: 800, color: "#fff" }}>爪</span>
              </div>
              <span style={{ fontSize: 17, fontWeight: 700, color: "#3D3660" }}>PawsMeme</span>
            </div>
            <p style={{ fontSize: 13, color: "#9D99BE", lineHeight: 1.7, maxWidth: 260, marginBottom: 16 }}>
              用 AI 把你家宝贝变成专属表情包。上传5张照片，选一种风格，2-4分钟出图。
            </p>
            <a href="mailto:hi@pawsmeme.ai" style={{
              display: "inline-flex", alignItems: "center", gap: 6,
              fontSize: 12, color: "#8B7CC8", textDecoration: "none",
            }}>
              <Mail size={13} /> hi@pawsmeme.ai
            </a>
          </div>

          {/* 功能 */}
          <div>
            <h4 style={{ fontSize: 13, fontWeight: 700, color: "#6B6490", marginBottom: 16 }}>功能</h4>
            <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
              {[
                { label: "4种风格",  href: "#styles" },
                { label: "效果展示", href: "#gallery" },
                { label: "立即生成", href: "/demo" },
              ].map((item) => (
                <button key={item.label} onClick={() => go(item.href)} style={{
                  background: "none", border: "none", cursor: "pointer",
                  textAlign: "left", fontSize: 13, color: "#9D99BE",
                  padding: 0, transition: "color 0.2s",
                }}>
                  {item.label}
                </button>
              ))}
            </div>
          </div>

          {/* 帮助 */}
          <div>
            <h4 style={{ fontSize: 13, fontWeight: 700, color: "#6B6490", marginBottom: 16 }}>帮助</h4>
            <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
              {[
                { label: "使用步骤", href: "#how" },
                { label: "拍摄指南", href: "#guide" },
                { label: "佳文的故事", href: "#story" },
              ].map((item) => (
                <button key={item.label} onClick={() => go(item.href)} style={{
                  background: "none", border: "none", cursor: "pointer",
                  textAlign: "left", fontSize: 13, color: "#9D99BE",
                  padding: 0,
                }}>
                  {item.label}
                </button>
              ))}
            </div>
          </div>

          {/* 技术 */}
          <div>
            <h4 style={{ fontSize: 13, fontWeight: 700, color: "#6B6490", marginBottom: 16 }}>技术支持</h4>
            <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
              {["Gemini 3 Pro Image Preview", "Google AI Studio", "OpenRouter API", "React + FastAPI"].map((item) => (
                <span key={item} style={{ fontSize: 12, color: "#9D99BE", display: "flex", alignItems: "center", gap: 6 }}>
                  <div style={{ width: 4, height: 4, borderRadius: "50%", background: "#B8AEE0", flexShrink: 0 }} />
                  {item}
                </span>
              ))}
            </div>
          </div>
        </div>

        {/* 底栏 */}
        <div style={{
          paddingTop: 24, borderTop: "1px solid #DDD8F0",
          display: "flex", justifyContent: "space-between", alignItems: "center",
          flexWrap: "wrap", gap: 12,
        }}>
          <div style={{ fontSize: 12, color: "#9D99BE" }}>
            © 2026 PawsMeme. All rights reserved.
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 4, fontSize: 12, color: "#9D99BE" }}>
            <span>Made with</span>
            <Heart size={12} color="#E8A4C0" fill="#E8A4C0" />
            <span>for pet lovers</span>
          </div>
        </div>
      </div>
    </footer>
  );
}
