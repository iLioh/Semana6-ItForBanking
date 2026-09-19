import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { Disclaimer } from './Disclaimer'

describe('Disclaimer', () => {
  it('muestra la advertencia académica precisa', () => {
    render(<Disclaimer />)
    expect(screen.getByRole('note')).toHaveTextContent('Demostración académica con datos simulados')
    expect(screen.getByRole('note')).toHaveTextContent('no constituyen decisiones crediticias')
  })
})
