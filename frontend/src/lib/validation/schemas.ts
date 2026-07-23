import { z } from 'zod';

const password = z
  .string()
  .min(8, 'A palavra-passe deve ter pelo menos 8 caracteres.')
  .max(128, 'A palavra-passe é demasiado longa.');

export const loginSchema = z.object({
  email: z.string().email('Indique um e-mail válido.'),
  password: z.string().min(1, 'Indique a palavra-passe.'),
});

export const otpSchema = z.object({
  code: z
    .string()
    .min(6, 'O código tem 6 dígitos.')
    .max(8, 'O código tem no máximo 8 dígitos.')
    .regex(/^\d+$/, 'O código só contém dígitos.'),
});

export const recoverySchema = z.object({
  email: z.string().email('Indique um e-mail válido.'),
});

export const resetSchema = z
  .object({
    password,
    password2: z.string(),
  })
  .refine((data) => data.password === data.password2, {
    path: ['password2'],
    message: 'As palavras-passe não coincidem.',
  });

export const changePasswordSchema = z
  .object({
    current_password: z.string().min(1, 'Indique a palavra-passe atual.'),
    password,
    password2: z.string(),
  })
  .refine((data) => data.password === data.password2, {
    path: ['password2'],
    message: 'As palavras-passe não coincidem.',
  });

export const acceptInvitationSchema = z
  .object({
    first_name: z.string().min(1, 'Indique o primeiro nome.').max(150),
    last_name: z.string().min(1, 'Indique o apelido.').max(150),
    phone: z.string().max(40).optional().or(z.literal('')),
    position: z.string().max(120).optional().or(z.literal('')),
    password,
    password2: z.string(),
    accept_terms: z.literal(true, { message: 'É necessário aceitar os termos.' }),
    accept_privacy_policy: z.literal(true, { message: 'É necessário aceitar a política de privacidade.' }),
  })
  .refine((data) => data.password === data.password2, {
    path: ['password2'],
    message: 'As palavras-passe não coincidem.',
  });

export const commentSchema = z.object({
  message: z.string().min(1, 'Escreva uma mensagem.').max(5000),
  visibility: z.enum(['public', 'internal']),
});

export const clientSchema = z.object({
  legal_name: z.string().min(1, 'Indique a denominação social.').max(255),
  commercial_name: z.string().max(255).optional().or(z.literal('')),
  nif: z.string().regex(/^\d{9}$/, 'O NIF tem 9 dígitos.'),
  entity_type: z.string().min(1),
  email: z.string().email('Indique um e-mail válido.').optional().or(z.literal('')),
  phone: z.string().max(40).optional().or(z.literal('')),
  city: z.string().max(120).optional().or(z.literal('')),
});

export const invitationSchema = z.object({
  client: z.string().min(1, 'Escolha o cliente.'),
  email: z.string().email('Indique um e-mail válido.'),
  role: z.enum(['owner', 'manager', 'accounting', 'employee', 'viewer']),
});

export const protocolSchema = z.object({
  client: z.string().min(1, 'Escolha o cliente.'),
  title: z.string().min(1, 'Indique o assunto.').max(255),
  description: z.string().max(4000).optional().or(z.literal('')),
  category: z.string().min(1),
  priority: z.enum(['low', 'normal', 'high', 'urgent']),
  due_date: z.string().optional().or(z.literal('')),
});

export const requirementSchema = z.object({
  title: z.string().min(1, 'Indique o documento pedido.').max(180),
  description: z.string().max(1000).optional().or(z.literal('')),
});

export type LoginInput = z.infer<typeof loginSchema>;
export type OtpInput = z.infer<typeof otpSchema>;
export type RecoveryInput = z.infer<typeof recoverySchema>;
export type ResetInput = z.infer<typeof resetSchema>;
export type ChangePasswordInput = z.infer<typeof changePasswordSchema>;
export type AcceptInvitationInput = z.infer<typeof acceptInvitationSchema>;
export type CommentInput = z.infer<typeof commentSchema>;
export type ClientInput = z.infer<typeof clientSchema>;
export type InvitationInput = z.infer<typeof invitationSchema>;
export type ProtocolInput = z.infer<typeof protocolSchema>;
export type RequirementInput = z.infer<typeof requirementSchema>;
