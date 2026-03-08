// Design: Mental Health App · 佳文的故事 · 情感叙事
import { motion } from "framer-motion";
import { useScrollAnimation } from "@/hooks/useScrollAnimation";
import { IMAGES } from "@/lib/images";
import { Heart, Camera } from "lucide-react";

const MEMORIES = [
  { image: IMAGES.realSmile,  caption: "草地上的笑脸",    desc: "每次看到你开心，整个世界都亮了", span: "row-span-2" },
  { image: IMAGES.realStick,  caption: "叼着树枝的冒险家", desc: "总是能找到最大的树枝，然后骄傲地叼回来" },
  { image: IMAGES.realCar,    caption: "车上的小乘客",     desc: "每次出门你都是最兴奋的那个" },
  { image: IMAGES.realDesk,   caption: "闭眼陪我加班",     desc: "闭着眼睛也陪着我到深夜" },
  { image: IMAGES.realBelly,  caption: "翻肚皮求摸摸",     desc: "这是你最信任我的时刻" },
];

export default function StorySection() {
  const { ref, isVisible } = useScrollAnimation(0.06);

  return (
    <section id="story" style={{ padding: "100px 0", background: "#F5F2FF" }}>
      <div ref={ref} style={{ maxWidth: 1100, margin: "0 auto", padding: "0 24px" }}>

        {/* 情感文案 + 主图 */}
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 56, alignItems: "center", marginBottom: 72 }}
          className="grid-cols-1 lg:grid-cols-2">

          <motion.div
            initial={{ opacity: 0, x: -32 }}
            animate={isVisible ? { opacity: 1, x: 0 } : {}}
            transition={{ duration: 0.8 }}
          >
            <div style={{
              display: "inline-flex", alignItems: "center", gap: 6,
              padding: "6px 16px", borderRadius: 20, marginBottom: 20,
              background: "rgba(232,164,192,0.12)", border: "1px solid rgba(232,164,192,0.25)",
            }}>
              <Heart size={13} color="#E890B8" />
              <span style={{ fontSize: 12, fontWeight: 600, color: "#E890B8" }}>佳文的故事</span>
            </div>

            <h2 style={{ fontSize: "clamp(26px,4vw,44px)", fontWeight: 800, color: "#3D3660", lineHeight: 1.2, marginBottom: 20 }}>
              每一个瞬间
              <br />
              <span className="text-gradient-warm">都值得被记住</span>
            </h2>

            <p style={{ fontSize: 16, color: "#9D99BE", lineHeight: 1.8, marginBottom: 16 }}>
              佳文是一只温暖的边牧混血，陪伴主人走过了无数个日夜。
              从草地上的奔跑，到沙发上的依偎，每一个瞬间都是不可替代的记忆。
            </p>

            <p style={{ fontSize: 15, color: "#9D99BE", lineHeight: 1.8, marginBottom: 24 }}>
              现在，用 AI 把这些瞬间变成表情包，让佳文的可爱和每天陪你聊天的朋友们分享。
              不只是纪念，更是日常的温柔。
            </p>

            <div style={{
              padding: "16px 20px", borderRadius: 14,
              background: "#F0EDF8",
              boxShadow: "4px 4px 12px #D0CCEC, -4px -4px 12px #FFFFFF",
              display: "flex", gap: 12, alignItems: "center",
            }}>
              <Heart size={20} color="#E8A4C0" style={{ flexShrink: 0 }} />
              <div>
                <div style={{ fontSize: 13, fontWeight: 700, color: "#3D3660" }}>为什么要做表情包？</div>
                <div style={{ fontSize: 12, color: "#9D99BE", marginTop: 4, lineHeight: 1.5 }}>
                  照片存在相册里，总感觉太严肃。但表情包，能让宝贝的可爱每天出现在你的聊天里。
                </div>
              </div>
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, x: 32 }}
            animate={isVisible ? { opacity: 1, x: 0 } : {}}
            transition={{ duration: 0.8, delay: 0.15 }}
          >
            <div style={{
              background: "#F0EDF8",
              borderRadius: 24,
              boxShadow: "12px 12px 30px #D0CCEC, -12px -12px 30px #FFFFFF",
              padding: 8,
            }}>
              <img
                src={IMAGES.story}
                alt="佳文与主人"
                style={{ width: "100%", borderRadius: 18, display: "block" }}
              />
            </div>
          </motion.div>
        </div>

        {/* 照片回忆墙 */}
        <motion.div
          initial={{ opacity: 0, y: 32 }}
          animate={isVisible ? { opacity: 1, y: 0 } : {}}
          transition={{ delay: 0.3 }}
        >
          <div style={{
            display: "flex", alignItems: "center", gap: 8, marginBottom: 20,
          }}>
            <Camera size={18} color="#8B7CC8" />
            <h3 style={{ fontSize: 18, fontWeight: 700, color: "#3D3660" }}>真实记忆</h3>
            <div style={{ flex: 1, height: 1, background: "#DDD8F0" }} />
          </div>

          <div style={{
            display: "grid",
            gridTemplateColumns: "repeat(3,1fr)",
            gridAutoRows: "200px",
            gap: 12,
          }} className="auto-rows-[180px] sm:auto-rows-[220px]">
            {MEMORIES.map((mem, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 20 }}
                animate={isVisible ? { opacity: 1, y: 0 } : {}}
                transition={{ delay: 0.4 + i * 0.08 }}
                style={{
                  position: "relative", borderRadius: 16, overflow: "hidden",
                  gridRow: i === 0 ? "span 2" : "span 1",
                  boxShadow: "4px 4px 12px #D0CCEC, -4px -4px 12px #FFFFFF",
                }}
                className="group"
              >
                <img
                  src={mem.image} alt={mem.caption}
                  style={{ position: "absolute", inset: 0, width: "100%", height: "100%", objectFit: "cover", transition: "transform 0.5s" }}
                />
                <div style={{
                  position: "absolute", inset: 0,
                  background: "linear-gradient(to top, rgba(61,54,96,0.65), transparent)",
                }} />
                <div style={{ position: "absolute", bottom: 0, left: 0, right: 0, padding: "12px 14px" }}>
                  <div style={{ fontSize: 13, fontWeight: 700, color: "#fff" }}>{mem.caption}</div>
                  <div style={{ fontSize: 11, color: "rgba(255,255,255,0.7)", marginTop: 3 }}>{mem.desc}</div>
                </div>
              </motion.div>
            ))}
          </div>
        </motion.div>

        {/* AI 未来视觉 */}
        <motion.div
          initial={{ opacity: 0, y: 32 }}
          animate={isVisible ? { opacity: 1, y: 0 } : {}}
          transition={{ delay: 0.6 }}
          style={{ marginTop: 48 }}
        >
          <div style={{ position: "relative", borderRadius: 24, overflow: "hidden",
            boxShadow: "8px 8px 24px #D0CCEC, -8px -8px 24px #FFFFFF" }}>
            <img src={IMAGES.futureAi} alt="AI宠物未来" style={{ width: "100%", display: "block" }} />
            <div style={{
              position: "absolute", inset: 0,
              background: "linear-gradient(90deg, rgba(61,54,96,0.82) 0%, rgba(61,54,96,0.5) 50%, transparent 100%)",
            }} />
            <div style={{ position: "absolute", inset: 0, display: "flex", alignItems: "center", padding: "32px 40px" }}>
              <div style={{ maxWidth: 420 }}>
                <div style={{
                  display: "inline-flex", alignItems: "center", gap: 6,
                  padding: "5px 14px", borderRadius: 20, marginBottom: 16,
                  background: "rgba(232,164,192,0.2)", border: "1px solid rgba(232,164,192,0.3)",
                }}>
                  <Heart size={12} color="#E8A4C0" />
                  <span style={{ fontSize: 11, fontWeight: 600, color: "#E8A4C0" }}>未来愿景</span>
                </div>
                <h3 style={{ fontSize: "clamp(18px,3vw,28px)", fontWeight: 800, color: "#fff", marginBottom: 12 }}>
                  让宝贝的快乐，成为你每天的表情
                </h3>
                <p style={{ fontSize: 14, color: "rgba(255,255,255,0.7)", lineHeight: 1.7 }}>
                  未来，每一次聊天都有宝贝陪着你。不只是照片，而是一套活灵活现的专属表情包。
                </p>
              </div>
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
