"use client";
import {useEffect,useRef,useState} from "react";
import {useRouter} from "next/navigation";
import {Flag,Send,UserX,Video} from "lucide-react";
import {api} from "@/lib/api";
import type {Conversation,Message} from "@/lib/types";
import {useRealtime} from "./realtime-provider";
import {Button,Textarea} from "./ui";
import {formatDate} from "@/lib/utils";

export function ChatView({conversationId}:{conversationId:string}){
 const [conversation,setConversation]=useState<Conversation|null>(null);const [messages,setMessages]=useState<Message[]>([]);const [text,setText]=useState("");const [error,setError]=useState("");const bottom=useRef<HTMLDivElement>(null);const router=useRouter();const {on}=useRealtime();
 async function load(){const [c,m]=await Promise.all([api<Conversation>(`/conversations/${conversationId}`),api<any>(`/conversations/${conversationId}/messages`)]);setConversation(c);const values=(m.results||m).slice().reverse();setMessages(values);const last=values.at(-1);if(last)await api(`/conversations/${conversationId}/read`,{method:"POST",body:JSON.stringify({message_id:last.id})})}
 useEffect(()=>{load();return on("message.created",(m:Message)=>{if(m.conversation===conversationId){setMessages(x=>x.some(v=>v.id===m.id)?x:[...x,m]);api(`/conversations/${conversationId}/read`,{method:"POST",body:JSON.stringify({message_id:m.id})}).catch(()=>{})}})},[conversationId]);
 useEffect(()=>bottom.current?.scrollIntoView({behavior:"smooth"}),[messages]);
 async function send(){if(!text.trim())return;const value=text;setText("");try{await api(`/conversations/${conversationId}/messages/send`,{method:"POST",body:JSON.stringify({client_message_id:crypto.randomUUID(),text:value})})}catch(e:any){setText(value);setError(e.message)}}
 async function call(){try{const r=await api<any>("/calls",{method:"POST",body:JSON.stringify({conversation_id:conversationId})});router.push(`/calls/${r.id}`)}catch(e:any){setError(e.message)}}
 async function block(){if(!conversation||!confirm(`Chặn ${conversation.other_user.display_name}?`))return;await api(`/users/${conversation.other_user.public_id}/block`,{method:"POST"});router.push("/messages")}
 async function report(){if(!conversation)return;const description=prompt("Mô tả ngắn nội dung cần báo cáo:")||"";const target=messages.at(-1)?.id||conversationId;try{await api("/reports",{method:"POST",body:JSON.stringify({reported_user_public_id:conversation.other_user.public_id,target_type:messages.length?"message":"profile",target_id:target,reason_code:"harassment",description})});setError("Đã gửi báo cáo tới đội ngũ kiểm duyệt.")}catch(e:any){setError(e.message)}}
 if(!conversation)return <div className="chat-loading">Đang tải…</div>;
 return <section className="chat-panel"><header className="chat-header"><div className="mini-avatar">{conversation.other_user.primary_photo?.public_url?<img src={conversation.other_user.primary_photo.public_url} alt=""/>:conversation.other_user.display_name[0]}</div><div className="grow"><b>{conversation.other_user.display_name}</b><small>Kết nối riêng tư</small></div><Button variant="ghost" title="Gọi video" onClick={call}><Video/></Button><Button variant="ghost" title="Báo cáo" onClick={report}><Flag/></Button><Button variant="ghost" title="Chặn" onClick={block}><UserX/></Button></header><div className="messages">{messages.map(m=><div key={m.id} className={`bubble ${m.sender_public_id===conversation.other_user.public_id?"theirs":"mine"}`}><p>{m.text}</p><small>{formatDate(m.created_at)}</small></div>)}<div ref={bottom}/></div>{error&&<div className="error-inline">{error}</div>}<div className="composer"><Textarea rows={1} maxLength={2000} value={text} onChange={e=>setText(e.target.value)} onKeyDown={e=>{if(e.key==="Enter"&&!e.shiftKey){e.preventDefault();send()}}} placeholder="Nhập tin nhắn…"/><Button onClick={send}><Send size={18}/></Button></div></section>
}
