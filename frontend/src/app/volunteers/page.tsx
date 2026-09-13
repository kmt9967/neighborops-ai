"use client";
import {useEffect,useState} from "react";
import {Heading} from "@/components/UI";
import {Volunteer,get} from "@/lib/api";
export default function Volunteers() {
  const [items, setItems] = useState<Volunteer[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    get<Volunteer[]>("/api/volunteers").then(setItems).catch(e => setError(e.message));
  }, []);

  return <>
    <Heading eyebrow="People power" title="Volunteers" subtitle="Availability, transport, capabilities, and current workload in one place."/>
    {error && <div className="notice error">{error}</div>}
    <div className="volunteer-list">{items.map(v => <div className="card volunteer" key={v.id}>
      <div className="avatar">{v.name.split(" ").map(x => x[0]).join("")}</div>
      <h2>{v.name}</h2>
      <span className={`pill ${v.availability ? "APPROVED" : "NEW"}`}>{v.availability ? "AVAILABLE" : "UNAVAILABLE"}</span>
      <p>{v.availability ? "Available for assignment" : "Currently unavailable"}</p>
      <div className="kv"><span>Transport</span><span>{v.transport_type}</span></div>
      <div className="kv"><span>Capacity</span><span>{v.max_capacity}</span></div>
      <div className="kv"><span>Current workload</span><span>{v.current_load} {v.current_load === 1 ? "task" : "tasks"}</span></div>
      <div className="chips">{v.skills.map(s => <span className="chip" key={s}>{s}</span>)}</div>
    </div>)}</div>
  </>;
}
