import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import { apiLogin, apiLogout, setAuthToken } from '../../api/client';
import { AuthUser, LoginCredentials, LoginResponse } from '../../api/types';

interface AuthState {
  user: AuthUser | null;
  accessToken: string | null;
  expiresAt: number | null;
  status: 'idle' | 'loading' | 'succeeded' | 'failed';
  error: string | null;
}

const STORAGE_KEY_USER = 'ei_analyst_user';
const STORAGE_KEY_TOKEN = 'ei_auth_token';

const loadInitialAuth = (): { user: AuthUser | null; token: string | null } => {
  try {
    const rawUser = sessionStorage.getItem(STORAGE_KEY_USER);
    const token = sessionStorage.getItem(STORAGE_KEY_TOKEN);
    const user = rawUser ? (JSON.parse(rawUser) as AuthUser) : null;
    if (token) setAuthToken(token);
    return { user, token };
  } catch {
    return { user: null, token: null };
  }
};

const initialAuth = loadInitialAuth();

const initialState: AuthState = {
  user: initialAuth.user,
  accessToken: initialAuth.token,
  expiresAt: null,
  status: 'idle',
  error: null,
};

export const loginThunk = createAsyncThunk<LoginResponse, LoginCredentials>(
  'auth/login',
  async (credentials: LoginCredentials, { rejectWithValue }) => {
    try {
      const response = await apiLogin(credentials);
      sessionStorage.setItem(STORAGE_KEY_TOKEN, response.accessToken);
      sessionStorage.setItem(STORAGE_KEY_USER, JSON.stringify(response.user));
      setAuthToken(response.accessToken);
      return response;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Authentication failed';
      return rejectWithValue(message);
    }
  }
);

export const logoutThunk = createAsyncThunk('auth/logout', async () => {
  await apiLogout();
  sessionStorage.removeItem(STORAGE_KEY_TOKEN);
  sessionStorage.removeItem(STORAGE_KEY_USER);
  setAuthToken(null);
});

export const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    clearAuthError: (state) => {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(loginThunk.pending, (state) => {
        state.status = 'loading';
        state.error = null;
      })
      .addCase(loginThunk.fulfilled, (state, action: PayloadAction<LoginResponse>) => {
        state.status = 'succeeded';
        state.accessToken = action.payload.accessToken;
        state.user = action.payload.user;
        state.expiresAt = Date.now() + action.payload.expiresInSeconds * 1000;
        state.error = null;
      })
      .addCase(loginThunk.rejected, (state, action) => {
        state.status = 'failed';
        state.error = (action.payload as string) || 'Authentication failed';
      })
      .addCase(logoutThunk.fulfilled, (state) => {
        state.user = null;
        state.accessToken = null;
        state.expiresAt = null;
        state.status = 'idle';
        state.error = null;
      });
  },
});

export const { clearAuthError } = authSlice.actions;
export default authSlice.reducer;
