describe('WorkNet Login', () => {
  it('should login successfully with test credentials', () => {
    cy.visit('http://localhost:8080');
    
    cy.get('[data-cy="username"], input[placeholder*="Username"], input[placeholder*="Usern ame"], input[name="username"], input[type="text"]')
      .first()
      .click()
      .type('test@example.com');
    
    cy.get('[data-cy="password"], input[placeholder*="Password"], input[type="password"], input[name="password"]')
      .first()
      .click()
      .type('password123');
    
    cy.get('[data-cy="signin"], button:contains("Sign in"), button[type="submit"], [role="button"]:contains("Sign in")')
      .first()
      .click();
    
    cy.url().should('not.include', '/login');
    cy.contains('Agents', { timeout: 10000 }).should('be.visible');
  });
});

