// Contract fields mirrored from backend document_service.FIELDS (keep in sync).
export const FIELDS = [
  { key: "contract_number", label: "Номер договора" },
  { key: "sign_date", label: "Дата подписания" },
  { key: "order_number", label: "Номер приказа" },
  { key: "order_date", label: "Дата приказа" },
  { key: "citizenship", label: "Гражданство" },
  { key: "full_name", label: "ФИО нанимателя" },
  { key: "birth_date", label: "Дата рождения" },
  { key: "room_number", label: "Номер комнаты" },
  { key: "contract_end_date", label: "Срок договора (до)" },
  { key: "registration_address", label: "Адрес регистрации" },
  { key: "passport_number", label: "Паспорт: номер" },
  { key: "passport_issue_date", label: "Паспорт: дата выдачи" },
  { key: "passport_valid_until", label: "Паспорт: срок действия" },
  { key: "passport_issued_by", label: "Паспорт: кем выдан" },
  { key: "id_number", label: "Идентификационный номер (ИИН)" },
  { key: "phone", label: "Номер телефона" },
];

export const FIELD_MAP = Object.fromEntries(FIELDS.map((f) => [f.key, f.label]));

export function mapRowsToStudents(rows, mapping) {
  return rows.map((row) => {
    const s = {};
    for (const [key, col] of Object.entries(mapping)) {
      if (col) s[key] = row[col] ?? "";
    }
    for (const f of FIELDS) if (!(f.key in s)) s[f.key] = "";
    return s;
  });
}
