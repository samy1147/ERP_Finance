'use client';

import Layout from '../components/Layout';
import { Toaster } from 'react-hot-toast';

export default function RootTemplate({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <>
      <Layout>{children}</Layout>
      <Toaster position="top-right" />
    </>
  );
}
