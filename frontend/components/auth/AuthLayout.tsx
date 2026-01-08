
import React from 'react';

interface AuthLayoutProps {
  children: React.ReactNode;
  title: string;
  subtitle?: string;
}

const AuthLayout: React.FC<AuthLayoutProps> = ({ children, title, subtitle }) => {
  return (
    <div className="min-h-screen flex flex-col md:flex-row bg-slate-50">
      {/* Left Side - Hero/Brand */}
      <div className="md:w-1/2 bg-primary relative overflow-hidden flex flex-col justify-center items-center text-white p-12">
        {/* Background Abstract Shapes */}
        <div className="absolute top-0 left-0 w-full h-full opacity-10 pointer-events-none">
             <div className="absolute top-10 right-10 w-20 h-20 rounded-full border-4 border-white"></div>
             <div className="absolute bottom-20 left-10 w-32 h-32 rounded-full bg-white blur-3xl"></div>
             {/* Dot Pattern */}
             <div className="absolute top-10 right-10 grid grid-cols-5 gap-2">
                {[...Array(25)].map((_, i) => <div key={i} className="w-1 h-1 bg-white rounded-full"></div>)}
             </div>
        </div>
        <div className="absolute bottom-0 left-0 w-full h-64 bg-gradient-to-t from-black/20 to-transparent"></div>

        <div className="relative z-10 max-w-md text-center md:text-left">
           <div className="mb-8 animate-fadeIn">
                <h1 className="text-4xl md:text-5xl font-bold mb-4">환영합니다!</h1>
                <p className="text-primary-lightest text-lg leading-relaxed">
                    AI 기반 모의 면접 솔루션으로<br/>당신의 꿈에 한 발짝 더 다가가세요.
                </p>
           </div>
        </div>
      </div>

      {/* Right Side - Form */}
      <div className="md:w-1/2 flex items-center justify-center p-6 animate-slideInFromRight">
        <div className="w-full max-w-md bg-white p-8 rounded-2xl shadow-sm border border-slate-100">
            <div className="mb-8">
                <h2 className="text-2xl font-bold text-slate-800">{title}</h2>
                {subtitle && <p className="text-slate-500 mt-2">{subtitle}</p>}
            </div>
            {children}
        </div>
      </div>
    </div>
  );
};

export default AuthLayout;
