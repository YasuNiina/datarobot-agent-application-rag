import { useMutation, useQuery } from '@tanstack/react-query';
import { listProviders, authorizeProvider, getOAuthCallback } from './requests';
import { oauthKeys } from './keys';
import { IOAuthProvider, IOAuthAuthorizeResponse, OAuthAuthorizeCallback } from './types';

export const useOauthProviders = () => {
  return useQuery<IOAuthProvider[], Error>({
    queryKey: oauthKeys.all,
    queryFn: () => listProviders(),
  });
};

export const useAuthorizeProvider = () => {
  return useMutation<IOAuthAuthorizeResponse, Error, { providerId: string; redirect_uri: string }>({
    mutationFn: ({ providerId, redirect_uri }) => authorizeProvider(providerId, { redirect_uri }),
  });
};

export const useOauthCallback = (query: string, enabled: boolean) => {
  return useQuery<OAuthAuthorizeCallback, Error>({
    queryKey: ['oauthCallback', query],
    queryFn: () => getOAuthCallback(query),
    enabled,
    retry: false,
  });
};
