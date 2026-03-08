// Design: Mental Health App · Neumorphism · Calm Pastel
import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Menu, X, Sparkles } from "lucide-react";
import { Link } from "wouter";

const NAV_ITEMS = [
  { label: "首页",     href: "#hero" },
  { label: "4种风格",  href: "#styles" },
  { label: "效果展示", href: "#gallery" },
  { label: "使用步骤", href: "#how" },
  { label: "拍摄指南", href: "#guide" },
  { label: "佳文的故事", href: "#story" },
];

export default function Navbar() {
  const [scrolled, setScrolled]     = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [active, setActive]         = useState("#hero");

  useEffect(() => {
    const onScroll = () => {
      setScrolled(window.scrollY > 60);
      for (let i = NAV_ITEMS.length - 1; i >= 0; i--) {
        const el = document.querySelector(NAV_ITEMS[i].href);
        if (el && el.getBoundingClientRect().top <= 120) {
          setActive(NAV_ITEMS[i].href);
          break;
        }
      }
    };
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  const go = (href: string) => {
    setMobileOpen(false);
    document.querySelector(href)?.scrollIntoView({ behavior: "smooth" });
  };

  return (
    <>
      <motion.nav
        initial={{ y: -80 }}
        animate={{ y: 0 }}
        transition={{ duration: 0.5, ease: "easeOut" }}
        style={{
          position: "fixed", top: 0, left: 0, right: 0, zIndex: 50,
          background: scrolled ? "rgba(245,242,255,0.88)" : "transparent",
          backdropFilter: scrolled ? "blur(20px)" : "none",
          borderBottom: scrolled ? "1px solid #DDD8F0" : "none",
          transition: "all 0.4s ease",
        }}
      >
        <div style={{ maxWidth: 1200, margin: "0 auto", padding: "0 20px" }}>
          <div style={{
            display: "flex", alignItems: "center", justifyContent: "space-between",
            height: 64,
          }}>
            {/* Logo */}
            <button onClick={() => go("#hero")} style={{
              display: "flex", alignItems: "center", gap: 10,
              background: "none", border: "none", cursor: "pointer",
            }}>
              <div style={{
                width: 36, height: 36, borderRadius: 10,
                background: "linear-gradient(135deg, #8B7CC8, #E8A4C0)",
                display: "flex", alignItems: "center", justifyContent: "center",
                boxShadow: "0 4px 12px rgba(139,124,200,0.4)",
              }}>
                <span style={{ fontSize: 13, fontWeight: 800, color: "#fff" }}>爪</span>
              </div>
              <span style={{ fontSize: 17, fontWeight: 700, color: "#3D3660" }}>PawsMeme</span>
            </button>

            {/* Desktop nav */}
            <div style={{ display: "flex", alignItems: "center", gap: 2 }} className="hidden lg:flex">
              {NAV_ITEMS.map((item) => (
                <button key={item.href} onClick={() => go(item.href)} style={{
                  position: "relative", padding: "8px 14px",
                  background: "none", border: "none", cursor: "pointer",
                  fontSize: 13, fontWeight: 500,
                  color: active === item.href ? "#8B7CC8" : "#9D99BE",
                  borderRadius: 10, transition: "color 0.2s",
                }}>
                  {item.label}
                  {active === item.href && (
                    <motion.div layoutId="nav-pill" style={{
                      position: "absolute", inset: 0, borderRadius: 10,
                      background: "rgba(139,124,200,0.08)",
                    }} transition={{ type: "spring", bounce: 0.2, duration: 0.5 }} />
                  )}
                </button>
              ))}
            </div>

            {/* CTA */}
            <div className="hidden lg:block">
              <Link href="/demo">
                <span style={{
                  display: "inline-flex", alignItems: "center", gap: 6,
                  padding: "10px 22px", borderRadius: 12,
                  background: "linear-gradient(135deg, #8B7CC8, #E8A4C0)",
                  color: "#fff", fontSize: 13, fontWeight: 700,
                  cursor: "pointer", textDecoration: "none",
                  boxShadow: "0 4px 16px rgba(139,124,200,0.35)",
                  transition: "box-shadow 0.2s",
                }}>
                  <Sparkles size={14} />
                  立即生成表情包
                </span>
              </Link>
            </div>

            {/* Mobile toggle */}
            <button
              onClick={() => setMobileOpen(!mobileOpen)}
              className="lg:hidden"
              style={{
                background: "none", border: "none", cursor: "pointer",
                color: "#8B7CC8", padding: 6,
              }}
            >
              {mobileOpen ? <X size={22} /> : <Menu size={22} />}
            </button>
          </div>
        </div>
      </motion.nav>

      {/* Mobile menu */}
      <AnimatePresence>
        {mobileOpen && (
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            style={{
              position: "fixed", inset: 0, zIndex: 40, paddingTop: 72,
              background: "rgba(245,242,255,0.97)", backdropFilter: "blur(20px)",
            }}
            className="lg:hidden"
          >
            <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 8, padding: "20px 24px" }}>
              {NAV_ITEMS.map((item, i) => (
                <motion.button
                  key={item.href}
                  initial={{ opacity: 0, y: 16 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.07 }}
                  onClick={() => go(item.href)}
                  style={{
                    width: "100%", padding: "14px 0",
                    background: "none", border: "none", borderBottom: "1px solid #EAE6F8",
                    fontSize: 16, fontWeight: 500, cursor: "pointer",
                    color: active === item.href ? "#8B7CC8" : "#6B6490",
                  }}
                >
                  {item.label}
                </motion.button>
              ))}
              <Link href="/demo">
                <motion.span
                  initial={{ opacity: 0, y: 16 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: NAV_ITEMS.length * 0.07 }}
                  onClick={() => setMobileOpen(false)}
                  style={{
                    display: "flex", alignItems: "center", justifyContent: "center", gap: 8,
                    marginTop: 12, width: "100%", padding: "16px 0",
                    background: "linear-gradient(135deg, #8B7CC8, #E8A4C0)",
                    color: "#fff", borderRadius: 14, fontSize: 16, fontWeight: 700,
                    cursor: "pointer", textDecoration: "none",
                    boxShadow: "0 6px 20px rgba(139,124,200,0.35)",
                  }}
                >
                  <Sparkles size={18} /> 立即生成表情包
                </motion.span>
              </Link>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}
