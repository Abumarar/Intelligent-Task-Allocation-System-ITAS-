import { useMemo, useState } from "react";

export default function TagInput({
    value,
    onChange,
    placeholder = "Add a skill and press Enter",
}: {
    value: string[];
    onChange: (next: string[]) => void;
    placeholder?: string;
}) {
    const [text, setText] = useState("");

    const normalized = useMemo(
        () => value.map((v) => v.trim()).filter(Boolean),
        [value],
    );

    const add = () => {
        const t = text.trim();
        if (!t) return;
        const next = Array.from(new Set([...normalized, t]));
        onChange(next);
        setText("");
    };

    const remove = (tag: string) =>
        onChange(normalized.filter((t) => t !== tag));

    return (
        <div className="tag-input">
            <div className="tag-list">
                {normalized.map((tag) => (
                    <span key={tag} className="tag-chip">
                        {tag}
                        <button
                            className="tag-remove"
                            onClick={() => remove(tag)}
                            type="button"
                            aria-label={`Remove ${tag}`}
                        >
                            x
                        </button>
                    </span>
                ))}
            </div>

            <div className="tag-field">
                <input
                    className="tag-text"
                    value={text}
                    placeholder={placeholder}
                    aria-label={placeholder}
                    onChange={(e) => setText(e.target.value)}
                    onKeyDown={(e) => {
                        if (e.key === "Enter") {
                            e.preventDefault();
                            add();
                        }
                    }}
                />
                <button
                    type="button"
                    className="btn btn-ghost btn-small"
                    onClick={add}
                    disabled={!text.trim()}
                >
                    Add
                </button>
            </div>
        </div>
    );
}
