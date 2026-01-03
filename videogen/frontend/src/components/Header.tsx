'use client';

import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { UserCircle } from 'lucide-react';

export function Header() {
    return (
        <header className="border-b border-border/70 bg-card/70 backdrop-blur-lg sticky top-0 z-50 shadow-[var(--shadow-soft)]">
            <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
                <Link href="/dashboard" className="flex items-center gap-2">
                    <div className="h-7 w-7 rounded-lg bg-primary/90 flex items-center justify-center shadow-[var(--shadow-soft)]">
                        <span className="text-primary-foreground font-bold text-xs">CS</span>
                    </div>
                    <span className="font-bold text-lg tracking-tight">Core Safety</span>
                </Link>
                <div className="flex items-center gap-4">
                    <div className="h-8 w-8 rounded-full bg-secondary/80 border border-border/60 flex items-center justify-center text-muted-foreground">
                        <UserCircle className="h-5 w-5" />
                    </div>
                </div>
            </div>
        </header>
    );
}
