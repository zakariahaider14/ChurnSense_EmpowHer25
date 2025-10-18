import { COOKIE_NAME } from "@shared/const";
import { getSessionCookieOptions } from "./_core/cookies";
import { systemRouter } from "./_core/systemRouter";
import { publicProcedure, protectedProcedure, router } from "./_core/trpc";
import { z } from "zod";

export const appRouter = router({
  system: systemRouter,

  auth: router({
    me: publicProcedure.query(opts => opts.ctx.user),
    logout: publicProcedure.mutation(({ ctx }) => {
      const cookieOptions = getSessionCookieOptions(ctx.req);
      ctx.res.clearCookie(COOKIE_NAME, { ...cookieOptions, maxAge: -1 });
      return {
        success: true,
      } as const;
    }),
  }),

  churn: router({
    queryChurnRate: protectedProcedure
      .input(z.object({ query: z.string() }))
      .mutation(async ({ input }) => {
        // This will be implemented to call the Gemini agent
        // For now, return a placeholder response
        return {
          summary: "Fetching churn analysis from the agent...",
          churnRate: 0,
          customerCount: 0,
        };
      }),
  }),
});

export type AppRouter = typeof appRouter;

