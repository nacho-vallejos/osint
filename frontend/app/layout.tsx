import './globals.css';
import 'reactflow/dist/style.css';

export const metadata = {
  title: 'OSINT Platform',
  description: 'Open Source Intelligence Platform for data collection and visualization',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className="bg-slate-900">{children}</body>
    </html>
  )
}
