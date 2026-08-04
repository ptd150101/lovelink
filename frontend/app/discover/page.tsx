"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Profile } from "@/lib/types";
import { ProfileCard } from "@/components/profile-card";
import { Button, Empty, Field, Input, Select } from "@/components/ui";

type Choice = [string, string];
type Ref = {
  provinces: { code: string; name: string }[];
  occupations: { id: string; name: string }[];
  choices: Record<string, Choice[]>;
};

type Filters = {
  min_age: number | string;
  max_age: number | string;
  min_height: string;
  max_height: string;
  gender: string[];
  province: string[];
  hometown: string[];
  occupation: string[];
  education: string[];
  income: string[];
  goal: string[];
  verified: boolean;
  has_photo: boolean;
  active_within_days: string;
  sort: string;
};

const multiKeys: (keyof Filters)[] = [
  "gender",
  "province",
  "hometown",
  "occupation",
  "education",
  "income",
  "goal",
];

const defaults: Filters = {
  min_age: 18,
  max_age: 40,
  min_height: "",
  max_height: "",
  gender: [],
  province: [],
  hometown: [],
  occupation: [],
  education: [],
  income: [],
  goal: [],
  verified: false,
  has_photo: true,
  active_within_days: "",
  sort: "recommended",
};

function MultiCheck({
  label,
  values,
  options,
  onChange,
}: {
  label: string;
  values: string[];
  options: { value: string; label: string }[];
  onChange: (values: string[]) => void;
}) {
  return (
    <fieldset className="multi-filter">
      <legend>{label}</legend>
      <div className="multi-filter-options">
        {options.map((option) => (
          <label className="check" key={option.value}>
            <input
              type="checkbox"
              checked={values.includes(option.value)}
              onChange={(event) =>
                onChange(
                  event.target.checked
                    ? [...values, option.value]
                    : values.filter((value) => value !== option.value),
                )
              }
            />
            {option.label}
          </label>
        ))}
      </div>
    </fieldset>
  );
}

export default function Discover() {
  const [items, setItems] = useState<Profile[]>([]);
  const [reference, setReference] = useState<Ref | null>(null);
  const [loading, setLoading] = useState(true);
  const [next, setNext] = useState<string | null>(null);
  const [filters, setFilters] = useState<Filters>(defaults);
  const [filterOpen, setFilterOpen] = useState(false);

  function query(current = filters) {
    const params = new URLSearchParams();
    Object.entries(current).forEach(([key, value]) => {
      if (Array.isArray(value)) {
        value.forEach((item) => params.append(key, item));
      } else if (value !== "" && value !== false) {
        params.set(key, String(value));
      }
    });
    return params;
  }

  async function load(
    current = filters,
    append = false,
    url?: string,
  ) {
    setLoading(true);
    try {
      const response = await api<any>(
        url
          ? url.replace(/^.*\/api\/v1/, "")
          : `/discover?${query(current)}`,
      );
      setItems((existing) =>
        append
          ? [...existing, ...(response.results || [])]
          : response.results || response,
      );
      setNext(response.next || null);
      if (typeof window !== "undefined" && !append) {
        history.replaceState(null, "", `/discover?${query(current)}`);
      }
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    api<Ref>("/reference-data").then(setReference);
    const params = new URLSearchParams(location.search);
    const restored: Filters = {
      ...defaults,
      gender: [],
      province: [],
      hometown: [],
      occupation: [],
      education: [],
      income: [],
      goal: [],
    };
    for (const key of Object.keys(restored) as (keyof Filters)[]) {
      if (multiKeys.includes(key)) {
        const values = params
          .getAll(key)
          .flatMap((value) => value.split(","))
          .filter(Boolean);
        (restored[key] as string[]) = values;
      } else if (params.has(key)) {
        if (key === "verified" || key === "has_photo") {
          (restored[key] as boolean) = params.get(key) === "true";
        } else {
          (restored[key] as string | number) = params.get(key) || "";
        }
      }
    }
    setFilters(restored);
    void load(restored);
  }, []);

  function set<K extends keyof Filters>(key: K, value: Filters[K]) {
    setFilters((current) => ({ ...current, [key]: value }));
  }

  const filtersUi = (
    <>
      <h2>Bộ lọc</h2>
      <div className="two">
        <Field label="Tuổi từ">
          <Input
            type="number"
            min={18}
            max={99}
            value={filters.min_age}
            onChange={(event) => set("min_age", event.target.value)}
          />
        </Field>
        <Field label="Đến">
          <Input
            type="number"
            min={18}
            max={99}
            value={filters.max_age}
            onChange={(event) => set("max_age", event.target.value)}
          />
        </Field>
      </div>
      <div className="two">
        <Field label="Cao từ">
          <Input
            type="number"
            min={120}
            max={230}
            value={filters.min_height}
            onChange={(event) => set("min_height", event.target.value)}
          />
        </Field>
        <Field label="Đến">
          <Input
            type="number"
            min={120}
            max={230}
            value={filters.max_height}
            onChange={(event) => set("max_height", event.target.value)}
          />
        </Field>
      </div>
      {reference && (
        <>
          <MultiCheck
            label="Giới tính"
            values={filters.gender}
            options={reference.choices.genders.map(([value, label]) => ({
              value,
              label,
            }))}
            onChange={(values) => set("gender", values)}
          />
          <MultiCheck
            label="Nơi ở"
            values={filters.province}
            options={reference.provinces.map((item) => ({
              value: item.code,
              label: item.name,
            }))}
            onChange={(values) => set("province", values)}
          />
          <MultiCheck
            label="Quê quán"
            values={filters.hometown}
            options={reference.provinces.map((item) => ({
              value: item.code,
              label: item.name,
            }))}
            onChange={(values) => set("hometown", values)}
          />
          <MultiCheck
            label="Nghề nghiệp"
            values={filters.occupation}
            options={reference.occupations.map((item) => ({
              value: item.id,
              label: item.name,
            }))}
            onChange={(values) => set("occupation", values)}
          />
          <MultiCheck
            label="Học vấn"
            values={filters.education}
            options={reference.choices.education.map(([value, label]) => ({
              value,
              label,
            }))}
            onChange={(values) => set("education", values)}
          />
          <MultiCheck
            label="Thu nhập"
            values={filters.income}
            options={reference.choices.income.map(([value, label]) => ({
              value,
              label,
            }))}
            onChange={(values) => set("income", values)}
          />
          <MultiCheck
            label="Mục tiêu"
            values={filters.goal}
            options={reference.choices.goals.map(([value, label]) => ({
              value,
              label,
            }))}
            onChange={(values) => set("goal", values)}
          />
        </>
      )}
      <Field label="Hoạt động gần đây">
        <Select
          value={filters.active_within_days}
          onChange={(event) =>
            set("active_within_days", event.target.value)
          }
        >
          <option value="">Không giới hạn</option>
          <option value="1">Trong 24 giờ</option>
          <option value="3">Trong 3 ngày</option>
          <option value="7">Trong 7 ngày</option>
          <option value="30">Trong 30 ngày</option>
        </Select>
      </Field>
      <label className="check">
        <input
          type="checkbox"
          checked={filters.has_photo}
          onChange={(event) => set("has_photo", event.target.checked)}
        />
        Chỉ hồ sơ có ảnh
      </label>
      <label className="check">
        <input
          type="checkbox"
          checked={filters.verified}
          onChange={(event) => set("verified", event.target.checked)}
        />
        Chỉ hồ sơ tích xanh
      </label>
      <Button
        className="full"
        onClick={() => {
          void load();
          setFilterOpen(false);
        }}
      >
        Áp dụng
      </Button>
      <Button
        variant="ghost"
        className="full"
        onClick={() => {
          const reset: Filters = {
            ...defaults,
            gender: [],
            province: [],
            hometown: [],
            occupation: [],
            education: [],
            income: [],
            goal: [],
          };
          setFilters(reset);
          void load(reset);
          setFilterOpen(false);
        }}
      >
        Xóa bộ lọc
      </Button>
    </>
  );

  return (
    <div className="page wide">
      <div className="page-heading">
        <div>
          <span className="eyebrow">Khám phá</span>
          <h1>Tìm người phù hợp</h1>
        </div>
        <div className="discover-heading-actions">
          <Button
            className="mobile-filter"
            variant="secondary"
            onClick={() => setFilterOpen(true)}
          >
            Bộ lọc
          </Button>
          <Select
            value={filters.sort}
            onChange={(event) => {
              const updated = { ...filters, sort: event.target.value };
              setFilters(updated);
              void load(updated);
            }}
          >
            <option value="recommended">Phù hợp nhất</option>
            <option value="recent">Mới hoạt động</option>
            <option value="newest">Hồ sơ mới</option>
            <option value="age_asc">Tuổi tăng dần</option>
          </Select>
        </div>
      </div>
      <div className="discover-layout">
        <aside className="filter-panel">{filtersUi}</aside>
        <section>
          {loading && !items.length ? (
            <div className="empty">Đang tải hồ sơ…</div>
          ) : items.length ? (
            <>
              <div className="profile-grid">
                {items.map((profile) => (
                  <ProfileCard key={profile.public_id} profile={profile} />
                ))}
              </div>
              {next && (
                <div className="load-more">
                  <Button
                    disabled={loading}
                    variant="secondary"
                    onClick={() => void load(filters, true, next)}
                  >
                    {loading ? "Đang tải…" : "Xem thêm"}
                  </Button>
                </div>
              )}
            </>
          ) : (
            <Empty
              title="Chưa tìm thấy hồ sơ"
              body="Hãy thử nới lỏng một vài điều kiện lọc."
            />
          )}
        </section>
      </div>
      {filterOpen && (
        <div className="modal-backdrop mobile-filter-modal">
          <aside className="filter-panel">
            <Button variant="ghost" onClick={() => setFilterOpen(false)}>
              Đóng
            </Button>
            {filtersUi}
          </aside>
        </div>
      )}
    </div>
  );
}
