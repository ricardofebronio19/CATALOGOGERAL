/**
 * Utilitários de formatação para exibição de dados
 */

export function formatCodigo(codigo, fornecedor) {
  if (!codigo) return '—';
  return fornecedor ? `${codigo} (${fornecedor})` : codigo;
}

export function formatAplicacao(app) {
  const parts = [app.veiculo, app.ano, app.motor].filter(Boolean);
  return parts.join(' • ') || '—';
}

export function formatWhatsApp(numero) {
  if (!numero) return null;
  const digits = numero.replace(/\D/g, '');
  return digits.startsWith('55') ? digits : '55' + digits;
}

export function formatPhone(numero) {
  if (!numero) return '—';
  const d = numero.replace(/\D/g, '');
  if (d.length === 11) return `(${d.slice(0, 2)}) ${d.slice(2, 7)}-${d.slice(7)}`;
  if (d.length === 10) return `(${d.slice(0, 2)}) ${d.slice(2, 6)}-${d.slice(6)}`;
  return numero;
}

export function truncate(text, max = 60) {
  if (!text) return '';
  return text.length > max ? text.slice(0, max) + '…' : text;
}
