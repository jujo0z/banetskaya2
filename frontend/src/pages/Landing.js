import React from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { ArrowRight, Flower2, Sparkles, Heart } from "lucide-react";

// Спокойная, светлая, цветочная тема 🌸
const PETALS = [
  { e: "🌸", top: "7%", left: "8%", size: "2.6rem", delay: "0s", op: 0.9 },
  { e: "🌷", top: "14%", left: "86%", size: "2.9rem", delay: "0.8s", op: 0.9 },
  { e: "🌼", top: "72%", left: "6%", size: "3.1rem", delay: "1.4s", op: 0.85 },
  { e: "🌺", top: "80%", left: "88%", size: "2.7rem", delay: "0.4s", op: 0.9 },
  { e: "🌻", top: "40%", left: "3%", size: "2.2rem", delay: "1.1s", op: 0.8 },
  { e: "💐", top: "34%", left: "92%", size: "2.4rem", delay: "1.8s", op: 0.8 },
  { e: "🌷", top: "90%", left: "46%", size: "2.2rem", delay: "0.6s", op: 0.75 },
  { e: "🪻", top: "5%", left: "50%", size: "2.1rem", delay: "1.5s", op: 0.75 },
  { e: "🌿", top: "58%", left: "94%", size: "2.3rem", delay: "0.2s", op: 0.7 },
  { e: "🌸", top: "60%", left: "2%", size: "1.9rem", delay: "2.1s", op: 0.7 },
];

export default function Landing() {
  const navigate = useNavigate();

  const enter = () => {
    try {
      sessionStorage.setItem("bnk_entered", "1");
    } catch (e) {
      // ignore
    }
    navigate("/");
  };

  return (
    <div className="min-h-screen w-full relative overflow-hidden bg-gradient-to-br from-rose-50 via-pink-50 to-violet-100 text-slate-700">
      {/* мягкие свечения */}
      <div className="pointer-events-none absolute -top-32 -left-24 h-[460px] w-[460px] rounded-full bg-pink-200/60 blur-[120px]" />
      <div className="pointer-events-none absolute -bottom-32 -right-24 h-[460px] w-[460px] rounded-full bg-violet-200/60 blur-[120px]" />
      <div className="pointer-events-none absolute top-1/3 left-1/2 h-[380px] w-[380px] -translate-x-1/2 rounded-full bg-amber-100/60 blur-[130px]" />

      {/* парящие цветочки */}
      {PETALS.map((p, i) => (
        <span
          key={i}
          className="pointer-events-none absolute select-none"
          style={{
            top: p.top,
            left: p.left,
            fontSize: p.size,
            opacity: p.op,
            animation: `bnkFloat 6s ease-in-out ${p.delay} infinite`,
            filter: "drop-shadow(0 6px 10px rgba(190,120,150,0.25))",
          }}
        >
          {p.e}
        </span>
      ))}

      <div className="relative mx-auto max-w-2xl px-6 py-16 flex flex-col items-center justify-center min-h-screen">
        {/* бренд */}
        <div className="flex items-center gap-3 mb-6">
          <div className="h-14 w-14 rounded-2xl bg-gradient-to-br from-rose-400 to-pink-500 grid place-items-center shadow-lg shadow-pink-300/50">
            <Flower2 className="h-8 w-8 text-white" />
          </div>
          <div className="leading-tight">
            <div className="font-heading text-3xl font-bold bg-gradient-to-r from-rose-500 to-fuchsia-500 bg-clip-text text-transparent">
              Банецкая
            </div>
            <div className="text-[11px] uppercase tracking-[0.25em] text-slate-400">
              Документы · с любовью
            </div>
          </div>
        </div>

        {/* карточка */}
        <div className="w-full rounded-[2rem] border border-white/70 bg-white/70 backdrop-blur-xl shadow-2xl shadow-pink-200/50 p-8 md:p-12 text-center">
          <div className="text-4xl md:text-5xl mb-4 tracking-widest">🌷 🌸 🌼</div>

          <h1 className="font-heading text-4xl md:text-5xl font-bold text-slate-800 leading-tight">
            Банецкая, не злись!{" "}
            <span className="inline-block align-middle">😊</span>
          </h1>

          <p className="text-slate-500 mt-5 max-w-md mx-auto leading-relaxed">
            Договоры и бланки заполняются сами — спокойно, красиво и без нервов.
            Загрузи Excel, а мы аккуратно напечатаем всё ровно по строчкам. 🌿
          </p>

          <div className="mt-6 inline-flex items-center gap-2 rounded-full bg-rose-100/70 px-4 py-1.5 text-sm text-rose-500">
            <Sparkles className="h-4 w-4" />
            <span>тепло, спокойно и по-домашнему</span>
            <Heart className="h-4 w-4 fill-rose-400 text-rose-400" />
          </div>

          <div className="mt-9 flex justify-center">
            <Button
              onClick={enter}
              size="lg"
              className="bg-gradient-to-r from-rose-400 to-pink-500 hover:from-rose-500 hover:to-pink-600 text-white font-semibold px-9 h-12 rounded-full shadow-lg shadow-pink-300/50 transition-transform hover:scale-[1.03]"
              data-testid="btn-start-work"
            >
              Начать работу <ArrowRight className="h-5 w-5 ml-2" />
            </Button>
          </div>
        </div>

        <p className="text-slate-400 text-xs mt-8 text-center">
          © Банецкая · сделано с 🌷 для тебя
        </p>
      </div>

      {/* анимация парения */}
      <style>{`
        @keyframes bnkFloat {
          0%, 100% { transform: translateY(0px) rotate(0deg); }
          50% { transform: translateY(-14px) rotate(8deg); }
        }
      `}</style>
    </div>
  );
}
