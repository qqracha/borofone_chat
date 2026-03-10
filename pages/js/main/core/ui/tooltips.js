// ==========================================
// DISCORD-LIKE TOOLTIPS
// ==========================================

const TOOLTIP_TARGET_SELECTOR = 'button[title], button[data-tooltip], .connection-status[title], .connection-status[data-tooltip]';
let discordTooltip = null;
let activeTooltipTarget = null;
let tooltipHideTimer = null;

function getTooltipText(target) {
    if (!target) return '';
    return (target.getAttribute('data-tooltip') || target.getAttribute('title') || '').trim();
}

function removeNativeTitle(target) {
    if (!target || !target.hasAttribute('title')) return;
    target.dataset.tooltipTitleBackup = target.getAttribute('title') || '';
    target.removeAttribute('title');
}

function restoreNativeTitle(target) {
    if (!target || !target.dataset.tooltipTitleBackup) return;
    if (!target.hasAttribute('title')) {
        target.setAttribute('title', target.dataset.tooltipTitleBackup);
    }
    delete target.dataset.tooltipTitleBackup;
}

function positionDiscordTooltip(target) {
    if (!discordTooltip || !target) return;

    const targetRect = target.getBoundingClientRect();
    const tooltipRect = discordTooltip.getBoundingClientRect();
    const gap = 10;
    const edgePadding = 8;

    let placement = target.dataset.tooltipPlacement;
    if (!placement) {
        const hasTopSpace = targetRect.top >= tooltipRect.height + gap + edgePadding;
        placement = hasTopSpace ? 'top' : 'bottom';
    }

    let top = placement === 'top'
        ? targetRect.top - tooltipRect.height - gap
        : targetRect.bottom + gap;
    let left = targetRect.left + (targetRect.width / 2) - (tooltipRect.width / 2);

    left = Math.max(edgePadding, Math.min(left, window.innerWidth - tooltipRect.width - edgePadding));
    top = Math.max(edgePadding, Math.min(top, window.innerHeight - tooltipRect.height - edgePadding));

    const arrowLeft = Math.max(
        12,
        Math.min(tooltipRect.width - 12, (targetRect.left + targetRect.width / 2) - left)
    );

    discordTooltip.dataset.placement = placement;
    discordTooltip.style.left = `${left}px`;
    discordTooltip.style.top = `${top}px`;
    discordTooltip.style.setProperty('--discord-tooltip-arrow-left', `${arrowLeft}px`);
}

function hideDiscordTooltip() {
    if (!discordTooltip || !activeTooltipTarget) return;
    restoreNativeTitle(activeTooltipTarget);
    discordTooltip.classList.remove('visible');
    activeTooltipTarget = null;
}

function queueHideDiscordTooltip() {
    clearTimeout(tooltipHideTimer);
    tooltipHideTimer = setTimeout(hideDiscordTooltip, 80);
}

function showDiscordTooltip(target) {
    const tooltipText = getTooltipText(target);
    if (!tooltipText || !discordTooltip) return;

    if (activeTooltipTarget === target) {
        clearTimeout(tooltipHideTimer);
        positionDiscordTooltip(target);
        return;
    }

    hideDiscordTooltip();
    removeNativeTitle(target);
    activeTooltipTarget = target;
    discordTooltip.textContent = tooltipText;
    discordTooltip.classList.add('visible');
    positionDiscordTooltip(target);
}

function findTooltipTarget(node) {
    if (!(node instanceof Element)) return null;
    return node.closest(TOOLTIP_TARGET_SELECTOR);
}

function initDiscordTooltips() {
    if (discordTooltip) return;

    discordTooltip = document.createElement('div');
    discordTooltip.className = 'discord-tooltip';
    discordTooltip.setAttribute('role', 'tooltip');
    document.body.appendChild(discordTooltip);

    document.addEventListener('mouseover', (event) => {
        const target = findTooltipTarget(event.target);
        if (!target) return;
        clearTimeout(tooltipHideTimer);
        showDiscordTooltip(target);
    }, true);

    document.addEventListener('mouseout', (event) => {
        if (!activeTooltipTarget) return;

        const fromTarget = findTooltipTarget(event.target);
        if (fromTarget !== activeTooltipTarget) return;

        const related = event.relatedTarget;
        if (related instanceof Element && activeTooltipTarget.contains(related)) return;
        queueHideDiscordTooltip();
    }, true);

    document.addEventListener('focusin', (event) => {
        const target = findTooltipTarget(event.target);
        if (!target) return;
        clearTimeout(tooltipHideTimer);
        showDiscordTooltip(target);
    }, true);

    document.addEventListener('focusout', (event) => {
        const target = findTooltipTarget(event.target);
        if (target && target === activeTooltipTarget) {
            queueHideDiscordTooltip();
        }
    }, true);

    document.addEventListener('pointerdown', () => {
        hideDiscordTooltip();
    }, true);

    window.addEventListener('scroll', () => {
        if (activeTooltipTarget) {
            positionDiscordTooltip(activeTooltipTarget);
        }
    }, true);

    window.addEventListener('resize', () => {
        if (activeTooltipTarget) {
            positionDiscordTooltip(activeTooltipTarget);
        }
    });
}

let currentUser = null;
let rooms = [];
let shouldRemoveAvatar = false;
let avatarCacheBuster = null;
let badgesInitialized = false;  // Флаг: badges загружены один раз
const REACTION_EMOJIS = ['👍', '❤️', '😂', '🔥', '🎉'];
const REACTION_TRIGGER_EMOJIS = ['😀', '😎', '✨', '🎯', '🫶', '😺', '🤙', '🌈'];
const ALL_EMOJI_OPTIONS = [
    { key: ':joy:', emoji: '😂' },
    { key: ':grin:', emoji: '😁' },
    { key: ':cow:', emoji: '🐮' },
    { key: ':heart_eyes:', emoji: '😍' },
    { key: ':thinking:', emoji: '🤔' },
    { key: ':thumbsup:', emoji: '👍' },
    { key: ':revolving_hearts:', emoji: '💞' },
    { key: ':fearful:', emoji: '😨' },
    { key: ':astonished:', emoji: '😮' },
    { key: ':rage:', emoji: '😡' },
];
let replyToMessage = null;
let activeReactionPickerFor = null;
