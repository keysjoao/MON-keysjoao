"use client"

import type React from "react"

import { useState, useEffect } from "react"
import { motion, AnimatePresence, useReducedMotion } from "framer-motion"
import { ChevronLeft, Plus, Sparkles, Check, AlertTriangle, Loader2 } from "lucide-react"

export interface Card {
    id: string
    title: string
    description?: string
    status: "completed" | "updates-found" | "syncing"
    details?: React.ReactNode
}

interface AnimatedCardStatusListProps {
    title?: string
    cards?: Card[]
    onSynchronize?: (cardId: string) => void
    onAddCard?: () => void
    onBack?: () => void
    className?: string
}

const defaultCards: Card[] = [
    { id: "1", title: "Import products from your store", status: "completed" },
    { id: "2", title: "Unique selling points", status: "completed" },
    { id: "3", title: "Primary customers", status: "completed" },
    { id: "4", title: "Common words & phrases", status: "updates-found" },
    { id: "5", title: "Company overview and offer details", status: "syncing" },
]

export function AnimatedCardStatusList({
    title = "Fundamentals",
    cards: initialCards = defaultCards,
    onSynchronize,
    onAddCard,
    onBack,
    className = "",
}: AnimatedCardStatusListProps = {}) {
    const [cards, setCards] = useState<Card[]>(initialCards)
    const [hoveredCard, setHoveredCard] = useState<string | null>(null)
    const [expandedCardId, setExpandedCardId] = useState<string | null>(null)
    const shouldReduceMotion = useReducedMotion()

    useEffect(() => {
        setCards(initialCards)
    }, [initialCards])

    const handleSynchronize = (e: React.MouseEvent, cardId: string) => {
        e.stopPropagation()
        if (onSynchronize) {
            onSynchronize(cardId)
        }

        setCards((prev) => prev.map((card) => (card.id === cardId ? { ...card, status: "syncing" as const } : card)))

        setTimeout(() => {
            setCards((prev) => prev.map((card) => (card.id === cardId ? { ...card, status: "completed" as const } : card)))
        }, 2500)
    }

    const handleCardClick = (cardId: string) => {
        setExpandedCardId(expandedCardId === cardId ? null : cardId)
    }

    const getStatusIcon = (status: Card["status"]) => {
        switch (status) {
            case "completed":
                return (
                    <motion.div
                        initial={{ scale: 0 }}
                        animate={{ scale: 1 }}
                        className="w-6 h-6 rounded-full bg-gradient-to-br from-success/70 to-success flex items-center justify-center shadow-[0_0_12px_var(--success)]"
                    >
                        <Check className="w-3.5 h-3.5 text-white" strokeWidth={3} />
                    </motion.div>
                )
            case "updates-found":
                return (
                    <motion.div
                        initial={{ scale: 0 }}
                        animate={{ scale: 1 }}
                        className="w-6 h-6 rounded-full bg-gradient-to-br from-warning/70 to-warning flex items-center justify-center shadow-[0_0_12px_var(--warning)]"
                    >
                        <AlertTriangle className="w-3.5 h-3.5 text-white" strokeWidth={2.5} />
                    </motion.div>
                )
            case "syncing":
                return (
                    <motion.div
                        initial={{ scale: 0 }}
                        animate={{ scale: 1 }}
                        className="w-6 h-6 rounded-full bg-gradient-to-br from-info/70 to-info flex items-center justify-center shadow-[0_0_12px_var(--info)]"
                    >
                        <motion.div
                            animate={{ rotate: 360 }}
                            transition={{ duration: 1, repeat: Number.POSITIVE_INFINITY, ease: "linear" }}
                        >
                            <Loader2 className="w-3.5 h-3.5 text-white" strokeWidth={2.5} />
                        </motion.div>
                    </motion.div>
                )
        }
    }

    const getStatusText = (status: Card["status"]) => {
        switch (status) {
            case "updates-found":
                return "Otimizações disponíveis"
            case "syncing":
                return "Sincronizando..."
            default:
                return null
        }
    }

    const getCardStyle = (status: Card["status"], isHovered: boolean) => {
        const baseStyle = "relative overflow-hidden rounded-2xl transition-all duration-300"

        switch (status) {
            case "updates-found":
                return `${baseStyle} bg-gradient-to-r from-warning/10 via-transparent to-warning/15 border border-warning/30`
            case "syncing":
                return `${baseStyle} bg-gradient-to-r from-info/10 via-transparent to-info/15 border border-info/30`
            default:
                return `${baseStyle} bg-muted/30 border border-border/40 ${isHovered ? "border-border/60" : ""}`
        }
    }

    const sortedCards = [...cards].sort((a, b) => {
        if (a.status === "completed" && b.status !== "completed") return -1
        if (a.status !== "completed" && b.status === "completed") return 1
        return 0
    })

    return (
        <div className={`w-full mx-auto p-4 sm:p-6 ${className}`}>
            <div className="relative rounded-3xl p-6 sm:p-8 bg-gradient-to-b from-background/80 to-background backdrop-blur-xl border border-border/50 shadow-2xl shadow-black/5 max-h-[85vh] overflow-y-auto">
                {/* Background decorativo sutil */}
                <div className="absolute inset-0 rounded-3xl overflow-hidden pointer-events-none">
                    <div className="absolute top-0 right-0 w-96 h-96 bg-gradient-to-bl from-primary/5 via-transparent to-transparent" />
                    <div className="absolute bottom-0 left-0 w-64 h-64 bg-gradient-to-tr from-muted/50 via-transparent to-transparent" />
                </div>

                <div className="relative flex items-center justify-between mb-8">
                    <motion.button
                        onClick={onBack}
                        className="p-2.5 rounded-xl bg-muted/50 cursor-pointer border border-border/50 hover:bg-muted hover:border-border transition-all duration-200"
                        whileHover={{ scale: 1.05, x: -2 }}
                        whileTap={{ scale: 0.95 }}
                    >
                        <ChevronLeft className="w-5 h-5 text-muted-foreground" />
                    </motion.button>

                    <div className="flex items-center gap-2">
                        <Sparkles className="w-5 h-5 text-primary/70" />
                        <h1 className="text-xl sm:text-2xl font-semibold text-foreground tracking-tight">{title}</h1>
                    </div>

                    <motion.button
                        onClick={onAddCard}
                        className="p-2.5 rounded-xl bg-primary/10 cursor-pointer border border-primary/20 hover:bg-primary/20 hover:border-primary/30 transition-all duration-200"
                        whileHover={{ scale: 1.05, rotate: 90 }}
                        whileTap={{ scale: 0.95 }}
                    >
                        <Plus className="w-5 h-5 text-primary" />
                    </motion.button>
                </div>

                {/* Cards */}
                <motion.div
                    className="relative space-y-3"
                    variants={{
                        visible: {
                            transition: {
                                staggerChildren: 0.06,
                                delayChildren: 0.1,
                            },
                        },
                    }}
                    initial="hidden"
                    animate="visible"
                >
                    <AnimatePresence>
                        {sortedCards.map((card, index) => (
                            <motion.div
                                key={card.id}
                                layout
                                layoutId={card.id}
                                variants={{
                                    hidden: { opacity: 0, y: 20, scale: 0.95 },
                                    visible: {
                                        opacity: 1,
                                        y: 0,
                                        scale: 1,
                                        transition: {
                                            type: "spring",
                                            stiffness: 300,
                                            damping: 30,
                                            duration: shouldReduceMotion ? 0.2 : undefined,
                                        },
                                    },
                                }}
                                exit={{
                                    opacity: 0,
                                    scale: 0.95,
                                    transition: { duration: 0.2 },
                                }}
                                className="relative cursor-pointer group"
                                onMouseEnter={() => setHoveredCard(card.id)}
                                onMouseLeave={() => setHoveredCard(null)}
                                onClick={() => handleCardClick(card.id)}
                            >
                                <motion.div
                                    className={getCardStyle(card.status, hoveredCard === card.id)}
                                    style={{ padding: "18px 20px" }}
                                    whileHover={{ y: -2 }}
                                    transition={{ duration: 0.2 }}
                                >
                                    {/* Efeito de brilho no hover */}
                                    <motion.div
                                        className="absolute inset-0 bg-gradient-to-r from-transparent via-white/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500"
                                        style={{ transform: "skewX(-20deg)" }}
                                        animate={hoveredCard === card.id ? { x: ["0%", "200%"] } : {}}
                                        transition={{ duration: 0.8, ease: "easeOut" }}
                                    />

                                    <div className="relative flex items-center justify-between gap-4">
                                        <div className="flex items-center gap-4 min-w-0">
                                            {/* Status Icon */}
                                            <div className="shrink-0">
                                                <AnimatePresence mode="wait">
                                                    <motion.div
                                                        key={card.status}
                                                        initial={{ scale: 0.5, opacity: 0 }}
                                                        animate={{ scale: 1, opacity: 1 }}
                                                        exit={{ scale: 0.5, opacity: 0 }}
                                                        transition={{ type: "spring", stiffness: 400, damping: 20 }}
                                                    >
                                                        {getStatusIcon(card.status)}
                                                    </motion.div>
                                                </AnimatePresence>
                                            </div>

                                            <div className="flex flex-col min-w-0">
                                                <span className="text-foreground font-medium text-sm sm:text-base truncate">{card.title}</span>
                                                {card.description && (
                                                    <span className="text-muted-foreground text-xs mt-0.5 truncate">{card.description}</span>
                                                )}
                                            </div>
                                        </div>

                                        {/* Status ou Botão */}
                                        <div className="flex items-center gap-3 shrink-0">
                                            <AnimatePresence mode="wait">
                                                {card.status === "updates-found" && hoveredCard === card.id && !expandedCardId ? (
                                                    <motion.button
                                                        key="sync-button"
                                                        initial={{ scale: 0.8, opacity: 0 }}
                                                        animate={{ scale: 1, opacity: 1 }}
                                                        exit={{ scale: 0.8, opacity: 0 }}
                                                        whileHover={{ scale: 1.05 }}
                                                        whileTap={{ scale: 0.95 }}
                                                        transition={{ type: "spring", stiffness: 400, damping: 20 }}
                                                        onClick={(e) => handleSynchronize(e, card.id)}
                                                        className="relative px-4 py-2 rounded-xl font-medium text-xs text-warning-foreground cursor-pointer overflow-hidden bg-gradient-to-r from-warning to-warning/80 shadow-[0_0_16px_var(--warning)] hover:shadow-[0_0_24px_var(--warning)] transition-shadow"
                                                    >
                                                        <span className="relative z-10">Sincronizar</span>
                                                    </motion.button>
                                                ) : getStatusText(card.status) ? (
                                                    <motion.span
                                                        key="status-text"
                                                        initial={{ opacity: 0 }}
                                                        animate={{ opacity: 1 }}
                                                        exit={{ opacity: 0 }}
                                                        className={`text-xs font-medium px-3 py-1.5 rounded-full hidden sm:inline-flex items-center gap-1.5 ${card.status === "updates-found"
                                                            ? "bg-warning/10 text-warning"
                                                            : "bg-info/10 text-info"
                                                            }`}
                                                    >
                                                        {card.status === "syncing" && (
                                                            <motion.span
                                                                className="w-1.5 h-1.5 rounded-full bg-current"
                                                                animate={{ opacity: [1, 0.3, 1] }}
                                                                transition={{ duration: 1.2, repeat: Number.POSITIVE_INFINITY }}
                                                            />
                                                        )}
                                                        {getStatusText(card.status)}
                                                    </motion.span>
                                                ) : null}
                                            </AnimatePresence>

                                            {card.details && (
                                                <motion.div
                                                    animate={{ rotate: expandedCardId === card.id ? 90 : 0 }}
                                                    transition={{ duration: 0.2 }}
                                                    className="p-1"
                                                >
                                                    <ChevronLeft className="w-4 h-4 text-muted-foreground rotate-180" />
                                                </motion.div>
                                            )}
                                        </div>
                                    </div>

                                    {/* Expanded Content */}
                                    <AnimatePresence>
                                        {expandedCardId === card.id && card.details && (
                                            <motion.div
                                                initial={{ height: 0, opacity: 0 }}
                                                animate={{ height: "auto", opacity: 1 }}
                                                exit={{ height: 0, opacity: 0 }}
                                                transition={{ duration: 0.3, ease: "easeInOut" }}
                                                className="overflow-hidden"
                                            >
                                                <div className="pt-4 mt-4 border-t border-border/30 text-sm text-muted-foreground">
                                                    {card.details}
                                                </div>
                                            </motion.div>
                                        )}
                                    </AnimatePresence>
                                </motion.div>
                            </motion.div>
                        ))}
                    </AnimatePresence>
                </motion.div>

            </div>
        </div>
    )
}
