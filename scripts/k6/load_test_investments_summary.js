import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  stages: [
    { duration: '30s', target: 20 }, // Ramp-up para 20 VUs em 30 segundos
    { duration: '1m', target: 50 },  // Estresse com 50 VUs por 1 minuto
    { duration: '30s', target: 100 }, // Pico com 100 VUs por 30 segundos
    { duration: '20s', target: 0 },   // Ramp-down
  ],
  thresholds: {
    http_req_duration: ['p(95)<200'], // 95% das requisições devem responder em < 200ms
    http_req_failed: ['rate<0.01'],    // Menos de 1% de falhas
  },
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';

export function setup() {
  const email = `perf_user_${Date.now()}@example.com`;
  const password = 'StrongPassword123!';

  // 1. Registrar usuário de teste de carga
  const registerRes = http.post(
    `${BASE_URL}/api/v1/auth/register`,
    JSON.stringify({ email, password }),
    { headers: { 'Content-Type': 'application/json' } }
  );

  check(registerRes, {
    'register status is 201': (r) => r.status === 201,
  });

  // 2. Fazer login e obter token JWT
  const loginRes = http.post(
    `${BASE_URL}/api/v1/auth/login`,
    JSON.stringify({ email, password }),
    { headers: { 'Content-Type': 'application/json' } }
  );

  check(loginRes, {
    'login status is 200': (r) => r.status === 200,
  });

  const token = loginRes.json('access_token');
  const authHeaders = {
    'Content-Type': 'application/json',
    Authorization: `Bearer ${token}`,
  };

  // 3. Cadastrar ativos de exemplo para consolidar o portfólio
  const sampleInvestments = [
    { ticker: 'PETR4', nome: 'Petrobras PN', classe: 'ACOES', quantidade: 100, preco_medio: 35.0, cotacao_atual: 38.5 },
    { ticker: 'VALE3', nome: 'Vale ON', classe: 'ACOES', quantidade: 50, preco_medio: 60.0, cotacao_atual: 62.0 },
    { ticker: 'HGLG11', nome: 'CSHG Logística', classe: 'FIIS', quantidade: 20, preco_medio: 160.0, cotacao_atual: 165.0 },
    { ticker: 'BTC', nome: 'Bitcoin', classe: 'CRIPTO', quantidade: 0.05, preco_medio: 300000.0, cotacao_atual: 350000.0 },
    { ticker: 'RESERVA', nome: 'Tesouro Selic', classe: 'RENDA_EMERGENCIAL', quantidade: 10, preco_medio: 1000.0, cotacao_atual: 1050.0 },
  ];

  sampleInvestments.forEach((inv) => {
    http.post(`${BASE_URL}/api/v1/investments/`, JSON.stringify(inv), { headers: authHeaders });
  });

  return { token };
}

export default function (data) {
  const headers = {
    'Content-Type': 'application/json',
    Authorization: `Bearer ${data.token}`,
  };

  const res = http.get(`${BASE_URL}/api/v1/investments/summary`, { headers });

  check(res, {
    'summary status is 200': (r) => r.status === 200,
    'has patrimonio_total': (r) => r.json('patrimonio_total') !== undefined,
    'has rentabilidade_percentual': (r) => r.json('rentabilidade_percentual') !== undefined,
    'has alocacao_por_classe': (r) => Array.isArray(r.json('alocacao_por_classe')),
  });

  sleep(0.1);
}
