// Логика формирования отображаемых значений слотов «Заявления».
// ДОЛЖНА совпадать с backend document_service.zayav_overlay_text.
const MONTHS = ["", "января", "февраля", "марта", "апреля", "мая", "июня",
  "июля", "августа", "сентября", "октября", "ноября", "декабря"];

export function splitRuDate(s) {
  if (!s) return ["", "", ""];
  const m = String(s).trim().match(/^(\d{1,2})[.\/-](\d{1,2})[.\/-](\d{2,4})$/);
  if (!m) return [String(s), "", ""];
  const d = m[1].padStart(2, "0");
  const mon = MONTHS[parseInt(m[2], 10)] || "";
  const y = m[3];
  return [d, mon, y];
}

export function zayavOverlayText(rec) {
  rec = rec || {};
  const g = (k) => {
    const v = rec[k];
    return v == null ? "" : String(v);
  };
  const fio = g("fio").trim();
  const by = g("birth_year").trim();
  const applicant = fio + (by ? `, ${by} г.р.` : "");
  const [sd, smon, sy] = splitRuDate(rec.sign_date);
  const sy2 = sy ? sy.slice(-2) : "";
  return {
    applicant,
    doc_name: g("doc_name"),
    passport_series: g("passport_series"),
    passport_number: g("passport_number"),
    passport_issued_by: g("passport_issued_by"),
    passport_issue_date: g("passport_issue_date"),
    reg_who: g("reg_who") || "одного",
    reg_count: g("reg_count") || "1",
    address_locality: g("address_locality"),
    res_street: g("res_street"),
    res_house: g("res_house"),
    res_korpus: g("res_korpus"),
    res_apartment: g("res_apartment"),
    stay_term: g("stay_term"),
    from_place: g("from_place"),
    basis: g("basis"),
    sign_day: sd,
    sign_month: smon,
    sign_year: sy2,
    area: g("area"),
    occupancy_count: g("occupancy_count"),
    minors_count: g("minors_count"),
  };
}

// Слот-наложение -> поле записи (для правки данных ПРЯМО в бланке).
// Прямое редактирование (input прямо на документе):
export const SLOT_FIELD = {
  applicant: "fio", // редактируем ФИО (год рождения — в панели слева)
  doc_name: "doc_name",
  passport_series: "passport_series",
  passport_number: "passport_number",
  passport_issued_by: "passport_issued_by",
  passport_issue_date: "passport_issue_date",
  reg_who: "reg_who",
  reg_count: "reg_count",
  address_locality: "address_locality",
  res_street: "res_street",
  res_house: "res_house",
  res_korpus: "res_korpus",
  res_apartment: "res_apartment",
  stay_term: "stay_term",
  from_place: "from_place",
  basis: "basis",
  area: "area",
  occupancy_count: "occupancy_count",
  minors_count: "minors_count",
};

// Слоты, которые вычисляются (дата) — клик фокусирует поле в панели слева.
export const SLOT_FOCUS = {
  sign_day: "sign_date",
  sign_month: "sign_date",
  sign_year: "sign_date",
};

