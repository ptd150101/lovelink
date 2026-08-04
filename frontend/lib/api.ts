const API=process.env.NEXT_PUBLIC_API_URL||"http://localhost:8000/api/v1";
function cookie(name:string){if(typeof document==="undefined")return "";return document.cookie.split("; ").find(x=>x.startsWith(name+"="))?.split("=").slice(1).join("=")||""}
let csrfReady=false;
export async function ensureCsrf(){if(csrfReady||typeof window==="undefined")return;await fetch(`${API}/auth/csrf`,{credentials:"include"});csrfReady=true}
export async function api<T=unknown>(path:string,init:RequestInit={}):Promise<T>{
 const method=(init.method||"GET").toUpperCase();if(!["GET","HEAD","OPTIONS"].includes(method))await ensureCsrf();
 const headers=new Headers(init.headers);if(init.body&&!headers.has("Content-Type")&&!(init.body instanceof FormData))headers.set("Content-Type","application/json");const token=decodeURIComponent(cookie("csrftoken"));if(token)headers.set("X-CSRFToken",token);
 const res=await fetch(`${API}${path}`,{...init,headers,credentials:"include",cache:"no-store"});
 if(res.status===204)return undefined as T;let data:any;try{data=await res.json()}catch{data={detail:"Phản hồi máy chủ không hợp lệ."}}
 if(!res.ok){const err=new Error(data.detail||"Yêu cầu thất bại.") as Error&{status?:number;data?:any};err.status=res.status;err.data=data;throw err}return data as T;
}
export async function uploadToSignedUrl(url:string,file:File,headers:Record<string,string>){const r=await fetch(url,{method:"PUT",body:file,headers});if(!r.ok)throw new Error("Không thể tải file lên kho lưu trữ.")}
