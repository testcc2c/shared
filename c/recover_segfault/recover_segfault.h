#ifndef RECOVER_SEGFAULT_H
#define RECOVER_SEGFAULT_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

/** Size of the buffer for ASM instruction description string */
#define ASM_INSTR_BUFSIZE 4096

struct segfault_memcontent {
    uintptr_t addr;
    uint8_t *data;
    size_t size;
};

#if defined(__linux__) || defined(__unix__) || defined(__posix__)
#    include <signal.h>

typedef mcontext_t asm_instr_context;
#    define asm_instr_ctx_reg(ctx, upper, ucfirst) ((ctx)->gregs[REG_##upper])
#    define asm_instr_ctx_regtype(upper, ucfirst) greg_t
#    define CONTEXT_FPREGS_PTYPE fpregset_t

#    if defined(__x86_64__)
#        define asm_instr_ctx_xmm_addr(ctx, num) (&((ctx)->fpregs->_xmm[(num)]))
#        define CONTEXT_FPREGS_TYPE __typeof__(*(fpregset_t)NULL)
#    elif defined(__i386__)
#        define asm_instr_ctx_xmm_addr(ctx, num) (&(((struct _fpstate*)(ctx)->fpregs)->_xmm[(num)]))
#        define CONTEXT_FPREGS_TYPE struct _fpstate
#    endif

#elif defined(_WIN32) || defined(WIN32) || defined(_WIN64) || defined(WIN64)
#    include <windows.h>

typedef CONTEXT asm_instr_context;
#    define asm_instr_ctx_reg(ctx, upper, ucfirst) ((ctx)->ucfirst)
#    define asm_instr_ctx_regtype(upper, ucfirst) typeof(((CONTEXT*)0)->ucfirst)

#    if defined(__x86_64__)
/* Get a XMM register with a fixed number */
#        define asm_instr_ctx_xmm_addr_const(ctx, num) (&((ctx)->Xmm##num))
#        define asm_instr_ctx_xmm_addr(ctx, num) (&(&((ctx)->Xmm0))[(num)])
#    elif defined(__i386__)
#        define asm_instr_ctx_xmm_addr(ctx, num) (&((ctx)->ExtendedRegisters[(10 + (num)) * 16]))
#    endif

#else
#    error "Unknown target OS"
#endif

#ifndef asm_instr_ctx_xmm_addr
#    define asm_instr_ctx_xmm_addr(ctx, num) asm_instr_ctx_xmm_addr_dyn(ctx, num)
#endif

int run_with_segfault_handler(const struct segfault_memcontent *memmap, size_t len, int (*fct)(void*), void *data);

void asm_printf(char *asm_instr, const char* format, ...)
    __attribute__ ((format (printf, 2, 3)));

bool run_mov_asm_instruction_p(asm_instr_context *ctx, uintptr_t data_addr, uint8_t *data, size_t datalen, char *asm_instr);
bool run_mov_asm_instruction(asm_instr_context *ctx, uintptr_t data_addr, uint8_t *data, size_t datalen);

#endif /* RECOVER_SEGFAULT_H */