"use client";
import {useCallback,useEffect,useState} from "react";
import Link from "next/link";
import {api} from "@/lib/api";
import type {Conversation} from "@/lib/types";
import {Alert,Button,Empty,Spinner} from "@/components/ui";
import {formatDate,safeErrorMessage} from "@/lib/utils";
export default function Messages(){
 const [items,setItems]=useState<Conversation[]>([]); const [loading,setLoading]=useState(true); const [error,setError]=useState(false);
 const load=useCallback(async()=>{setLoading(true);setError(false);try{const r=await api<any>("/conversations");setItems(r.results||r)}catch{setError(true)}finally{setLoading(false)}},[]);
 useEffect(()=>{void load()},[load]);
 return <div className="page"><div className="page-heading"><div><span className="eyebrow">Tin nhắn</span><h1>Hội thoại</h1></div></div>
 {loading?<p role="status"><Spinner/> Đang tải hội thoại…</p>:error?<Alert>Không thể tải hội thoại. <Button variant="secondary" onClick={()=>void load()}>Thử lại</Button></Alert>:items.length?<div className="conversation-list">{items.map(c=>{const photo=c.other_user.primary_photo?.thumbnail_url||c.other_user.primary_photo?.public_url;return<Link href={`/messages/${c.id}`} key={c.id}><div className="mini-avatar">{photo?<img src={photo} alt="" width={62} height={62} loading="lazy" decoding="async"/>:c.other_user.display_name[0]}</div><div className="grow"><b>{c.other_user.display_name}</b><p>{c.last_message?.text||"Bắt đầu trò chuyện"}</p></div><div className="conversation-meta"><small>{formatDate(c.last_message_at)}</small>{c.unread_count>0&&<span>{c.unread_count}</span>}</div></Link>})}</div>:<Empty title="Chưa có hội thoại" body="Cuộc trò chuyện mở sau khi hai bên cùng đồng ý kết nối." action={<div className="form-actions"><Link className="btn btn-primary" href="/discover">Khám phá hồ sơ</Link><Link className="btn btn-secondary" href="/connections">Xem kết nối</Link></div>}/>}</div>}
