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
  { key: "note", label: "Дополнительно (вручную)" },
];

// Moderation sections — custom clauses appended into specific parts of the contract.
export const SECTIONS = [
  { key: "extra_subject", title: "I. Предмет договора" },
  { key: "extra_tenant", title: "II. Права и обязанности нанимателя" },
  { key: "extra_landlord", title: "III. Права и обязанности наймодателя" },
  { key: "extra_liability", title: "IV. Ответственность сторон" },
  { key: "extra_term", title: "V. Срок действия договора" },
  { key: "extra_other", title: "VII. Прочие условия" },
];

export const FIELD_MAP = Object.fromEntries(FIELDS.map((f) => [f.key, f.label]));

// Logical grouping for the document editor (keys reference FIELDS).
export const FIELD_GROUPS = [
  {
    id: "contract",
    title: "Договор",
    icon: "FileSignature",
    keys: ["contract_number", "sign_date", "order_number", "order_date", "contract_end_date"],
  },
  {
    id: "tenant",
    title: "Наниматель",
    icon: "User",
    keys: ["full_name", "citizenship", "birth_date", "phone", "id_number"],
  },
  {
    id: "housing",
    title: "Проживание",
    icon: "Home",
    keys: ["room_number", "registration_address"],
  },
  {
    id: "passport",
    title: "Паспорт",
    icon: "BookUser",
    keys: ["passport_number", "passport_issue_date", "passport_valid_until", "passport_issued_by"],
  },
  {
    id: "extra",
    title: "Дополнительно",
    icon: "PlusCircle",
    keys: ["note"],
  },
];

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
