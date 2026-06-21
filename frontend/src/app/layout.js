import "./globals.css";

export const metadata = {
  title: "Zomato AI – Discover Your Perfect Restaurant",
  description: "India's smartest AI-powered restaurant recommendation engine. Get ranked, personalised picks powered by Groq LLM in under 5 seconds.",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        {/* Load Outfit font */}
        <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&display=swap" rel="stylesheet" />
        {/* Load Material Symbols separately to bypass Next.js combined font optimizer issues */}
        <link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@24,400,1,0" rel="stylesheet" />
      </head>
      <body>
        {children}
      </body>
    </html>
  );
}
