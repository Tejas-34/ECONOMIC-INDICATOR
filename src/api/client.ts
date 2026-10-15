import { TickerStreamPayload, LoginCredentials, LoginResponse } from './types';

import gdpGrowthMock from '../mocks/gdpGrowth.json';
import debtToGdpMock from '../mocks/debtToGdp.json';
import tradeBalanceMock from '../mocks/tradeBalance.json';
import gstCollectionMock from '../mocks/gstCollection.json';
import inflationMock from '../mocks/inflation.json';
import govtExpenditureMock from '../mocks/govtExpenditure.json';
import tickerFeedMock from '../mocks/tickerFeed.json';

const MOCK_MAP: Record<string, unknown> = {
  'gdp-growth': gdpGrowthMock,
  'debt-to-gdp': debtToGdpMock,
  'trade-balance': tradeBalanceMock,
  'gst-collection': gstCollectionMock,
  inflation: inflationMock,
  'govt-expenditure': govtExpenditureMock,
};

let inMemoryToken: string | null = null;

export const setAuthToken = (token: string | null) => {
  inMemoryToken = token;
};

export const getAuthToken = (): string | null => inMemoryToken;

const isMockMode = (): boolean => {
  return import.meta.env.VITE_USE_MOCKS !== 'false';
};

const getBaseUrl = (): string => {
  return import.meta.env.VITE_API_BASE_URL || '/api';
};

export class ApiError extends Error {
  public status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
    this.name = 'ApiError';
  }
}

export async function fetchIndicator<T = unknown>(id: string): Promise<T> {
  if (isMockMode()) {
    // Artificial small delay for realism
    await new Promise((resolve) => setTimeout(resolve, 80));
    const data = MOCK_MAP[id];
    if (!data) {
      throw new ApiError(`Indicator '${id}' not found in mock database`, 404);
    }
    return JSON.parse(JSON.stringify(data)) as T;
  }

  const response = await fetch(`${getBaseUrl()}/indicators/${id}`, {
    headers: {
      'Content-Type': 'application/json',
      ...(inMemoryToken ? { Authorization: `Bearer ${inMemoryToken}` } : {}),
    },
  });

  if (!response.ok) {
    throw new ApiError(
      `Failed to fetch indicator '${id}': ${response.statusText}`,
      response.status
    );
  }

  return response.json();
}

export async function fetchLatestTickerQuotes(): Promise<TickerStreamPayload> {
  if (isMockMode()) {
    await new Promise((resolve) => setTimeout(resolve, 50));
    return JSON.parse(JSON.stringify(tickerFeedMock)) as TickerStreamPayload;
  }

  const response = await fetch(`${getBaseUrl()}/ticker/latest`, {
    headers: {
      'Content-Type': 'application/json',
      ...(inMemoryToken ? { Authorization: `Bearer ${inMemoryToken}` } : {}),
    },
  });

  if (!response.ok) {
    throw new ApiError(`Failed to fetch ticker quotes: ${response.statusText}`, response.status);
  }

  return response.json();
}

export async function apiLogin(credentials: LoginCredentials): Promise<LoginResponse> {
  if (isMockMode()) {
    await new Promise((resolve) => setTimeout(resolve, 150));
    if (credentials.email && credentials.password) {
      const mockResponse: LoginResponse = {
        user: {
          id: 'usr_mock_001',
          email: credentials.email,
          name: 'Lead Macro Analyst',
          role: 'analyst',
        },
        accessToken: 'mock_jwt_token_analyst_2026',
        expiresInSeconds: 3600,
      };
      setAuthToken(mockResponse.accessToken);
      return mockResponse;
    }
    throw new ApiError('Invalid email or password', 401);
  }

  const response = await fetch(`${getBaseUrl()}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(credentials),
  });

  if (!response.ok) {
    throw new ApiError('Authentication failed', response.status);
  }

  const data: LoginResponse = await response.json();
  setAuthToken(data.accessToken);
  return data;
}

export async function apiLogout(): Promise<void> {
  setAuthToken(null);
  if (!isMockMode()) {
    try {
      await fetch(`${getBaseUrl()}/auth/logout`, { method: 'POST' });
    } catch {
      // Ignore network errors during sign-out cleanup
    }
  }
}
