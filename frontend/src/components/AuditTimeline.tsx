import type { AuditEvent } from "../api/types";

export function AuditTimeline({ events }: { events: AuditEvent[] }) {
  return (
    <section aria-label="Audit timeline" className="panel">
      <h3>Audit timeline</h3>
      {events.length === 0 ? <p>No audit events.</p> : null}
      <ol className="timeline">
        {events.map((event) => (
          <li key={event.eventId}>
            <span className="event-type">{event.eventType}</span>{" "}
            <span className="event-time">{event.createdAt}</span>
            <span className="event-meta">
              prompt {event.promptRunId}
              {event.actionId ? ` · action ${event.actionId}` : ""}
              {event.evidencePacket ? ` · packet ${event.evidencePacket}` : ""}
            </span>
          </li>
        ))}
      </ol>
    </section>
  );
}
