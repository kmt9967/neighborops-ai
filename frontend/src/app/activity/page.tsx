"use client";
import {useEffect,useState} from "react";
import {Heading,Timeline} from "@/components/UI";
import {Event,get} from "@/lib/api";
export default function ActivityPage(){const [items,setItems]=useState<Event[]>([]),[error,setError]=useState("");useEffect(()=>{get<Event[]>("/api/activity").then(setItems).catch(e=>setError(e.message))},[]);return <><Heading eyebrow="Transparent autonomy" title="Agent activity" subtitle="Every classification, inventory check, reservation, escalation, and human decision has a visible record."/>{error&&<div className="notice error">{error}</div>}<div className="card" style={{maxWidth:860}}><div className="card-head"><h2>Operations timeline</h2><span className="subtitle">Newest first</span></div><Timeline items={items}/></div></>}
