import { Badge, Card, type Tone } from '@/components/ui';
import { CHANGELOG, CHANGE_LABELS, type ChangeType } from '@/content/changelog';
import { formatDate } from '@/lib/utils/format';

/** Each change type gets a colour and reads as a small tag. */
const CHANGE_TONE: Record<ChangeType, Tone> = {
  new: 'success',
  improved: 'info',
  fix: 'warning',
};

/**
 * The "Novidades e correções" map. Reads the code-committed changelog so it
 * ships with each release, no backend required. The newest release is marked
 * as the current version.
 */
export function ChangelogView() {
  return (
    <div className="space-y-6">
      {CHANGELOG.map((release, index) => (
        <Card key={release.version} className="overflow-hidden">
          <div className="flex flex-wrap items-center gap-2 border-b border-mist px-5 py-4">
            <h2 className="text-sm font-semibold text-navy">
              v{release.version} — {release.title}
            </h2>
            {index === 0 ? <Badge tone="success">Versão atual</Badge> : null}
            <time className="ml-auto text-xs text-navy/45">{formatDate(release.date)}</time>
          </div>
          <ul className="divide-y divide-mist/60">
            {release.changes.map((change, changeIndex) => (
              <li key={changeIndex} className="flex items-start gap-3 px-5 py-3">
                <Badge tone={CHANGE_TONE[change.type]}>{CHANGE_LABELS[change.type]}</Badge>
                <p className="text-sm text-navy/80">{change.text}</p>
              </li>
            ))}
          </ul>
        </Card>
      ))}
    </div>
  );
}
