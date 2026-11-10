import React from "react";
import { Stamp } from "lucide-react";
import DocEditor from "@/components/DocEditor";

// Демо-значения для наглядного предпросмотра полей в редакторе
const SAMPLE = {
  reg_organ: "Отдел по гражданству и миграции Советского РУВД г. Минска",
  date_day: "01",
  date_month: "сентября",
  date_year: "26",
  number: "1234",
  fio: "Иванов Иван Иванович",
  fio2: "",
  birth: "2006 г., г. Минск",
  address: "г. Минск, пр-т Дзержинского, д. 85, ком. 902/2",
  address2: "",
  passport_series: "MP",
  passport_number: "3751195",
  issue_day: "05",
  issue_month: "10",
  issue_year: "22",
  issued_by: "Советским РУВД г. Минска",
  from_day: "01",
  from_month: "09",
  from_year: "26",
  to_day: "30",
  to_month: "06",
  to_year: "27",
  chief: "О.Н. Петрова",
};

export default function SoobshenieEditor() {
  return (
    <div className="p-6 lg:p-8 space-y-6" data-testid="soobshenie-editor-page">
      <div>
        <h1 className="text-3xl font-semibold tracking-tight flex items-center gap-3 text-slate-900">
          <Stamp className="h-8 w-8 text-[#EC4899]" /> Редактор сообщения
        </h1>
        <p className="text-muted-foreground mt-1 max-w-3xl">
          Двигайте тексты и поля, добавляйте линии — как в редакторах Формы 19/24 и «Заявления».
          Шаблон применяется в «Полной печати» сообщения. Данные полей показаны демонстрационно.
        </p>
      </div>
      <div className="rounded-lg border border-pink-100 bg-white p-2 lg:p-3 shadow-2xl">
        <DocEditor which="soobshenie" values={SAMPLE} singlePage />
      </div>
    </div>
  );
}
