import { Amplify } from 'aws-amplify';

const userPoolId = import.meta.env.VITE_COGNITO_USER_POOL_ID;
const userPoolClientId = import.meta.env.VITE_COGNITO_CLIENT_ID;

export const authConfigured = Boolean(userPoolId && userPoolClientId);

if (authConfigured) {
  const configuredUserPoolId = userPoolId as string;
  const configuredUserPoolClientId = userPoolClientId as string;

  Amplify.configure({
    Auth: {
      Cognito: {
        userPoolId: configuredUserPoolId,
        userPoolClientId: configuredUserPoolClientId,
      },
    },
  });
}
