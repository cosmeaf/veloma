import { Check, Circle } from 'lucide-react';

import { RequirementStatusBadge } from '@/components/status';
import { Card, CardHeader, EmptyState } from '@/components/ui';
import { formatDate } from '@/lib/utils/format';
import type { Requirement } from '@/types';

export function RequirementChecklist({ requirements, action }: { requirements: Requirement[]; action?: React.ReactNode }) {
  const pending = requirements.filter((item) => item.status === 'pending').length;

  return (
    <Card>
      <CardHeader
        title="Documentos solicitados"
        description={pending ? `${pending} por enviar` : 'Nada em falta'}
        action={action}
      />
      {requirements.length === 0 ? (
        <EmptyState title="Sem documentos solicitados" />
      ) : (
        <ul className="divide-y divide-mist/70">
          {requirements.map((requirement) => (
            <li key={requirement.id} className="flex items-center justify-between gap-4 px-5 py-3">
              <div className="flex items-start gap-3">
                {requirement.status === 'pending' ? (
                  <Circle className="mt-0.5 size-4 text-lilac" aria-hidden />
                ) : (
                  <Check className="mt-0.5 size-4 text-emerald-600" aria-hidden />
                )}
                <div>
                  <p className="text-sm font-medium text-navy">{requirement.title}</p>
                  {requirement.description ? (
                    <p className="mt-0.5 text-sm text-navy/55">{requirement.description}</p>
                  ) : null}
                  {requirement.due_date ? (
                    <p className="mt-0.5 text-xs text-navy/40">Prazo: {formatDate(requirement.due_date)}</p>
                  ) : null}
                </div>
              </div>
              <RequirementStatusBadge status={requirement.status} />
            </li>
          ))}
        </ul>
      )}
    </Card>
  );
}
