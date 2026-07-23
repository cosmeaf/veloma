import { Card, CardHeader, EmptyState } from '@/components/ui';
import { EVENT_LABELS, PROTOCOL_STATUS, formatDateTime, label } from '@/lib/utils/format';
import type { TimelineEvent } from '@/types';

function describe(event: TimelineEvent): string | null {
  if (event.event_type === 'status_changed' && event.new_value) {
    return `${label(PROTOCOL_STATUS, event.old_value)} → ${label(PROTOCOL_STATUS, event.new_value)}`;
  }
  return event.new_value || null;
}

export function ProtocolTimeline({ events }: { events: TimelineEvent[] }) {
  return (
    <Card>
      <CardHeader title="Histórico" description="Cada alteração fica registada." />
      {events.length === 0 ? (
        <EmptyState title="Sem registos" />
      ) : (
        <ol className="divide-y divide-mist/70">
          {events.map((event) => (
            <li key={event.id} className="flex items-start justify-between gap-4 px-5 py-3">
              <div>
                <p className="text-sm font-medium text-navy">{label(EVENT_LABELS, event.event_type)}</p>
                <p className="mt-0.5 text-sm text-navy/55">
                  {[event.actor_name_snapshot || 'Sistema', describe(event)].filter(Boolean).join(' · ')}
                </p>
              </div>
              <time className="text-xs whitespace-nowrap text-navy/40">{formatDateTime(event.created_at)}</time>
            </li>
          ))}
        </ol>
      )}
    </Card>
  );
}
