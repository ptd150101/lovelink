import {ButtonHTMLAttributes,InputHTMLAttributes,ReactNode,TextareaHTMLAttributes} from "react";
import {cn} from "@/lib/utils";
export function Button({className,variant="primary",...p}:ButtonHTMLAttributes<HTMLButtonElement>&{variant?:"primary"|"secondary"|"danger"|"ghost"}){return <button className={cn("btn",`btn-${variant}`,className)} {...p}/>}
export function Input({className,...p}:InputHTMLAttributes<HTMLInputElement>){return <input className={cn("input",className)} {...p}/>}
export function Textarea({className,...p}:TextareaHTMLAttributes<HTMLTextAreaElement>){return <textarea className={cn("input textarea",className)} {...p}/>}
export function Select({className,children,...p}:React.SelectHTMLAttributes<HTMLSelectElement>){return <select className={cn("input",className)} {...p}>{children}</select>}
export function Card({children,className=""}:{children:ReactNode;className?:string}){return <section className={cn("card",className)}>{children}</section>}
export function Field({label,children,error,hint}:{label:string;children:ReactNode;error?:string;hint?:string}){return <label className="field"><span>{label}</span>{children}{hint&&<small>{hint}</small>}{error&&<small className="error">{error}</small>}</label>}
export function Badge({children,tone="default"}:{children:ReactNode;tone?:"default"|"verified"|"success"|"warning"}){return <span className={`badge badge-${tone}`}>{children}</span>}
export function Empty({title,body,action}:{title:string;body:string;action?:ReactNode}){return <div className="empty"><h3>{title}</h3><p>{body}</p>{action}</div>}
export function Spinner(){return <span className="spinner" aria-label="Đang tải"/>}
