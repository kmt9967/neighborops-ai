export const API=process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
export type Resource={id:string;name:string;type:string;total_quantity:number;available_quantity:number;reserved_quantity:number;safety_threshold:number};
export type Volunteer={id:string;name:string;transport_type:string;availability:boolean;max_capacity:string;skills:string[];current_load:number};
export type Event={id:string;request_id:string|null;event_type:string;message:string;created_at:string;metadata:Record<string,unknown>};
export type Allocation={id:string;resource_id:string;quantity:number;volunteer_id:string|null;status:string};
export type Request={id:string;requester_name:string;category:string;description:string;household_size:number|null;location:string|null;urgency:string;status:string;structured_data:{requested_quantity?:number;delivery_required?:boolean};reasoning_summary:string|null;created_at:string;allocations?:Allocation[];events?:Event[];decisions?:{id:string;reason:string;selected_option:string|null}[];tasks?:{id:string;type:string;status:string;volunteer_id:string|null}[]};
export type Dashboard={organization:string;open_requests:number;pending_requests:number;auto_handled:number;human_review:number;available_volunteers:number;resources:Resource[];recent_requests:Request[];recent_events:Event[]};
export async function get<T>(path:string):Promise<T>{const r=await fetch(`${API}${path}`,{cache:"no-store"});if(!r.ok)throw new Error("Unable to reach the operations API. Start the backend and refresh.");return r.json()}
export async function post<T>(path:string,body?:unknown):Promise<T>{const r=await fetch(`${API}${path}`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(body||{})});const data=await r.json();if(!r.ok)throw new Error(typeof data.detail==="string"?data.detail:data.detail?.message||"Request failed");return data}
export const short=(id:string)=>id.startsWith("req-")?id.toUpperCase():id.slice(0,8).toUpperCase();
export const date=(value:string)=>new Date(value).toLocaleString("en-PK",{month:"short",day:"numeric",hour:"2-digit",minute:"2-digit"});
