import { useId, type ReactNode } from "react";
import "./MediaUpload.css";
type Props = { kind: "image" | "video"; title: string; description: string; hint: ReactNode; file?: File; preview?: string; generation: number; accept: string; inputLabel: string; selectLabel: string; actionLabel: string; clearLabel: string; disabled: boolean; compact?: boolean; onChoose: (file?: File) => void; onAnalyze: () => void; onReset: () => void };
export function MediaUpload(p: Props) {
    const id = useId();
    return (
        <div className={"upload-card media-upload-card " + (p.kind === "image" ? "image-upload-card" : "video-upload-card") + (p.compact ? " is-compact" : "")} role="region" aria-label={p.kind === "image" ? "Carga de imagen" : "Carga de video"}>
            <div className="upload-copy">
                <div className="upload-heading">
                    <span className="upload-glyph" aria-hidden="true">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">{p.kind === "image" ? <><rect x="3" y="3" width="18" height="18" rx="3" /><circle cx="8" cy="8" r="1.4" /><path d="m3 17 5-5 4 4 4-6 5 7" /></> : <><rect x="3" y="3" width="18" height="18" rx="3" /><path d="m10 8 6 4-6 4Z" /></>}</svg>
                    </span>
                    <div>
                        <h3>{p.title}</h3>
                        <p>{p.description}</p>
                    </div>
                </div>
                <div className="upload-selection">
                    <label className="file-label" htmlFor={id}>{p.selectLabel}
                        <input key={p.generation} id={id} aria-label={p.inputLabel} type="file" accept={p.accept} onChange={e => p.onChoose(e.target.files?.[0])} />
                    </label>
                    <div className="upload-hints">{p.hint}
                    </div>
                </div>
            </div>
            <div className="upload-review">
                <div className="upload-file-summary">
                    {p.preview && <img className="upload-preview" src={p.preview} alt="Vista previa de la imagen seleccionada" />}
                    <span className="filename" title={p.file?.name}>{p.file?.name ?? "Ningún archivo seleccionado"}</span>
                </div>
                <div className="upload-actions">{!p.compact && <button className="primary" disabled={p.disabled || !p.file} onClick={p.onAnalyze}>{p.actionLabel}<span aria-hidden="true">→</span></button>}{p.file && <button className="quiet" onClick={p.onReset}>{p.clearLabel}</button>}
                </div>
            </div>
        </div>
    );
}
