'use client';

import { Loader2, Pencil, X } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { useState } from 'react';
import { useForm } from 'react-hook-form';

import { Alert, Button, Card, CardHeader, Field, Input, Select } from '@/components/ui';
import type { ClientDetail } from '@/types';

const ENTITY_TYPES = [
  ['quotas', 'Sociedade por quotas'],
  ['unipessoal', 'Sociedade unipessoal'],
  ['eni', 'Empresário em nome individual'],
  ['independent', 'Trabalhador independente'],
  ['association', 'Associação'],
  ['foundation', 'Fundação'],
  ['condominium', 'Condomínio'],
  ['other', 'Outro'],
] as const;

type FormValues = {
  legal_name: string;
  commercial_name: string;
  nif: string;
  entity_type: string;
  activity_code: string;
  activity_description: string;
  email: string;
  phone: string;
  website: string;
  address_line: string;
  postal_code: string;
  city: string;
  district: string;
};

/**
 * Lets staff correct or complete a client's data after registration.
 * Collapsed by default; opens an inline form pre-filled with current values.
 */
export function EditClientCard({ client }: { client: ClientDetail }) {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const form = useForm<FormValues>({
    defaultValues: {
      legal_name: client.legal_name,
      commercial_name: client.commercial_name ?? '',
      nif: client.nif,
      entity_type: client.entity_type,
      activity_code: client.activity_code ?? '',
      activity_description: client.activity_description ?? '',
      email: client.email ?? '',
      phone: client.phone ?? '',
      website: client.website ?? '',
      address_line: client.address_line ?? '',
      postal_code: client.postal_code ?? '',
      city: client.city ?? '',
      district: client.district ?? '',
    },
  });

  async function onSubmit(values: FormValues) {
    setError(null);
    const response = await fetch(`/api/portal/clients/${client.id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(values),
    });
    const payload = await response.json().catch(() => ({}));
    if (!response.ok || !payload.success) {
      setError(payload.message ?? 'Não foi possível guardar as alterações.');
      return;
    }
    setOpen(false);
    router.refresh();
  }

  if (!open) {
    return (
      <div className="flex justify-end">
        <Button variant="secondary" size="sm" onClick={() => setOpen(true)}>
          <Pencil className="size-4" aria-hidden />
          Editar dados
        </Button>
      </div>
    );
  }

  return (
    <Card>
      <CardHeader
        title="Editar dados do cliente"
        description="Corrija ou complete a informação da empresa."
        action={
          <button type="button" onClick={() => setOpen(false)} aria-label="Fechar" className="text-navy/40 hover:text-navy">
            <X className="size-4" />
          </button>
        }
      />
      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4 px-5 py-4">
        {error ? <Alert>{error}</Alert> : null}
        <div className="grid gap-4 sm:grid-cols-2">
          <Field label="Denominação social">
            <Input {...form.register('legal_name')} />
          </Field>
          <Field label="Nome comercial">
            <Input {...form.register('commercial_name')} />
          </Field>
          <Field label="NIF">
            <Input {...form.register('nif')} inputMode="numeric" />
          </Field>
          <Field label="Tipo de entidade">
            <Select {...form.register('entity_type')}>
              {ENTITY_TYPES.map(([value, labelText]) => (
                <option key={value} value={value}>
                  {labelText}
                </option>
              ))}
            </Select>
          </Field>
          <Field label="CAE">
            <Input {...form.register('activity_code')} />
          </Field>
          <Field label="Atividade">
            <Input {...form.register('activity_description')} />
          </Field>
          <Field label="E-mail">
            <Input {...form.register('email')} type="email" />
          </Field>
          <Field label="Telefone">
            <Input {...form.register('phone')} />
          </Field>
          <Field label="Website">
            <Input {...form.register('website')} />
          </Field>
          <Field label="Morada">
            <Input {...form.register('address_line')} />
          </Field>
          <Field label="Código postal">
            <Input {...form.register('postal_code')} />
          </Field>
          <Field label="Cidade">
            <Input {...form.register('city')} />
          </Field>
          <Field label="Distrito">
            <Input {...form.register('district')} />
          </Field>
        </div>
        <div className="flex gap-2">
          <Button type="submit" disabled={form.formState.isSubmitting}>
            {form.formState.isSubmitting ? <Loader2 className="size-4 animate-spin" /> : null}
            Guardar alterações
          </Button>
          <Button type="button" variant="secondary" onClick={() => setOpen(false)}>
            Cancelar
          </Button>
        </div>
      </form>
    </Card>
  );
}
